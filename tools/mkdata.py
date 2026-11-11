#!/usr/bin/env python3
"""assets/ -> build/data/: everything the assembler includes (INCBIN) and the resource files of the disk.

    python tools/mkdata.py          (build.py runs it)

build/data/*.dat, *.dta, *.zx0 ...   blocks included by the sources (names as in the 1996 sources, lower case)
build/data/res_raw/NN_name.bin       the 73 resources (unpacked; build.py packs them) the game loads from the disk by number (see RES)
"""
import hashlib
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import zx0
import gfxconv as g
import textconv as t

LANG = os.environ.get('UFO2_LANG', 'ru')
AS = os.path.join(ROOT, 'assets')
OUT = os.path.join(ROOT, 'build', 'data')
CACHE = os.path.join(ROOT, 'build', 'cache')

# Resources of the disk in the order of their numbers (1..73): the game asks for a resource by number (READ in
# src/game/disk.asm). m = landscape set (tile properties + tile pictures), l = map, up = encyclopedia pictures.
RES = ("m2 m3 m4 m5 m10 m7 m8 m9 m6 m11 m12 m13 m14 m15 m16 m17 m18 m19 m20 l2 end l3 l4 l5a l5b l5c l5d l6a l6b l6c "
       "l6d x2 l7 l8a l8b l8c l8d l9 x3 l10a l10b l10c l10d l11 l12 l13 l14 l15 l19 l17 l18 l16 l20 "
       + ' '.join(f'up{i}' for i in range(1, 21))).split()
# Encyclopedia: page N (resource upN) shows three pictures gfx/pedia/x<number>.png
PEDIA = [17, 14, 39, 15, 13, 18, 21, 20, 36, 24, 40, 37, 38, 12, 11, 16, 10, 9, 1, 2, 8, 3, 19, 5, 4, 6, 7, 33, 26, 22,
         23, 34, 35, 42, 46, 45, 43, 44, 48, 47, 50, 49, 25, 41, 31, 27, 30, 28, 32, 55, 29, 51, 60, 57, 58, 56, 59,
         52, 53, 54]
UI = [('xearth', 24, 15), ('xweapon', 4, 30), ('xbutton', 4, 11), ('xsign', 3, 36), ('xparam', 3, 20), ('xkey', 12, 8),
      ('xlabel', 2, 52), ('xscan', 1, 12)]          # picture, width in bytes, height in character rows


def rd(*p):
    with open(os.path.join(AS, *p), 'rb') as f:
        return f.read()


def wr(name, data):
    path = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not (os.path.exists(path) and open(path, 'rb').read() == data):
        with open(path, 'wb') as f:
            f.write(data)
    return data


def pack(data):
    """ZX0 block (word length + stream) with a cache: optimal packing takes seconds per file."""
    os.makedirs(CACHE, exist_ok=True)
    key = os.path.join(CACHE, hashlib.sha1(b'zx0-1' + data).hexdigest())
    if os.path.exists(key):
        return open(key, 'rb').read()
    out = zx0.pack(data)
    with open(key, 'wb') as f:
        f.write(out)
    return out


def no_eded(data, step):
    """The 1996 intro converters never let two #ED bytes stand together (their first packer used #ED #ED as a mark)."""
    out = bytearray(data)
    for i in range(1, len(out)):
        if out[i] == 0xED and out[i - 1] == 0xED:
            out[i] = (out[i] + step) & 255
    return bytes(out)


def intro_set(prefix, first, count, wbytes, rows, step):
    out = b''
    for n in range(first, first + count):
        out += no_eded(g.plain(os.path.join(AS, 'gfx', 'intro', f'{prefix}{n}.png'), wbytes, rows), step)
    return out


def main():
    gfx = lambda *p: os.path.join(AS, 'gfx', *p)
    # ---- game: sprites
    wr('xsprites.dat', b''.join(g.plain(gfx('ui', n + '.png'), w, h * 8) for n, w, h in UI))
    wr('xmarker.dat', g.masked(gfx('sprites', 'xmarker.png'), 1, 4, 32))
    wr('xhero.dat', g.masked(gfx('sprites', 'xhero.png'), 10, 16, 24))
    wr('xhist.scr', rd('screens', 'xhist.scr'))
    wr('xfont.dat', rd('fonts', 'xfont.bin'))
    wr('xangles.dan', rd('tables', 'xangles.bin'))
    wr('xscales.dan', rd('tables', 'xscales.bin'))
    # ---- game: landscape sets and maps
    attrs, convs = g.read_tiles(os.path.join(AS, 'tiles.txt'))
    land = {n: g.masked(gfx('land', f'xm{n}.png'), g.FTYP[n], 16, 32) for n in range(21)}
    wr('xm0.zx0', pack(land[0]))
    wr('xm1.zx0', pack(land[1]))
    wr('xl0.zx0', pack(rd('maps', 'xl0.lnd')))
    wr('xl1.zx0', pack(rd('maps', 'xl1.lnd')))
    res = {}
    for n in range(2, 21):
        xa, xc = g.tile_tables(attrs, convs, n)
        res[f'm{n}'] = xa + xc + land[n]
    for f in os.listdir(os.path.join(AS, 'maps')):
        n = f[1:-4]
        if f.endswith('.lnd') and n in RES:
            res[n] = rd('maps', f)
    for i in range(20):
        res[f'up{i + 1}'] = b''.join(g.plain(gfx('pedia', f'x{PEDIA[i * 3 + k]}.png'), 28, 192) for k in range(3))
    res['x2'] = res['x3'] = b'1' * 16 + b'\r\n'          # two unused numbers (placeholders of 1996)
    # ---- texts
    tx = lambda n: t.load(os.path.join(AS, 'text', LANG, n + '.txt'))
    d = t.worder(tx('xword'), tx('xname'), tx('xmenu'), tx('xfopedia'), tx('xend'))
    for k, v in d.items():
        wr(k, v)
    ins, cm = t.instr(tx('xinstr'))
    wr('xinstr.dat', ins)
    wr('xinstrcm.dat', cm)
    # ---- title program
    for n in range(1, 5):
        wr(f'xi{n}.dta', pack(rd('screens', f'xi{n}.scr')))
    wr('m_ufo.dta', pack(rd('music', 'm_ufo.bin')))
    # ---- manual
    for n in range(1, 6):
        wr(f'xn{n}.dta', pack(rd('screens', f'xn{n}.scr')))
    wr('xnf1.dta', rd('fonts', 'xnf1.fon'))
    wr('xnf2.dta', rd('fonts', 'xnf2.fon'))
    # ---- intro
    wr('m_ivan2.$c', rd('music', 'm_ivan2.bin'))
    wr('xtitle.dat', no_eded(g.plain(gfx('intro', 'xtitle.png'), 16, 112), -1))
    for k in range(3):
        wr(f'xdemo{k}.dat', intro_set('xd', 1 + k * 8, 8, 16, 128, 1))
    wr('xdemos6.dat', intro_set('xs', 1, 56, 6, 48, -1))
    wr('xdemos7.dat', intro_set('xx', 1, 56, 6, 48, -1))
    wr('xdemotxt.dat', intro_set('xt', 1, 28, 24, 24, -1))
    # ---- ending
    wr('xend.mus', rd('music', 'xend.mus'))
    wr('xend1.scr', rd('screens', 'xend1.scr'))
    # ---- resources (the "end" one is added by build.py after the ending is assembled)
    for i, n in enumerate(RES):
        if n != 'end':
            wr(os.path.join('res_raw', f'{i + 1:02}_{n}.bin'), res[n])
    return res


if __name__ == '__main__':
    main()
    print('build/data ready')
