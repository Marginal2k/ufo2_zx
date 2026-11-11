#!/usr/bin/env python3
"""One-off: turn the author's archive (archive/UFO2_SRC) into the editable assets/ tree.

    python tools/import_archive.py

* 1-bit TIFs -> PNG (same pixels);
* CP866 texts -> UTF-8;
* things that are not in the archive (fonts of the game, compiled music, attribute parts of some screens) are cut
  out of the 1996 release (reference/, see tools/extract_ref.py);
* four files of the archive are newer than the release (xm11, the pictures of encyclopedia page 6, map xl18,
  one space in xword.txt): the release versions are taken, the archive ones are kept with the suffix "_archive".
"""
import os
import shutil
import struct
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import lpc
import gfxconv

A = os.path.join(ROOT, 'archive', 'UFO2_SRC')
R1 = os.path.join(ROOT, 'reference', 'disk1')
R2 = os.path.join(ROOT, 'reference', 'disk2')
OUT = os.path.join(ROOT, 'assets')


def rd(*p):
    with open(os.path.join(*p), 'rb') as f:
        return f.read()


def wr(rel, data):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


def png(src, rel):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.open(src).convert('1').save(path, optimize=True)


def png_from_rows(rows, wbytes, rel):
    """rows: bytes with ink = 1 -> PNG with black ink."""
    h = len(rows) // wbytes
    im = Image.frombytes('1', (wbytes * 8, h), bytes(b ^ 255 for b in rows))
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, optimize=True)


def unmask(data, bands, per_band, lines):
    """Inverse of gfxconv.masked: sprite data -> picture rows (32 bytes wide)."""
    rows = [bytearray(32) for _ in range(bands * 2 * lines)]
    p = 0
    for i in range(bands):
        for j in range(per_band):
            for k in range(lines):
                for m in range(2):
                    bb, aa = data[p], data[p + 1]
                    p += 2
                    rows[i * 2 * lines + k + lines][j * 2 + m] = bb
                    rows[i * 2 * lines + k][j * 2 + m] = aa ^ bb
    return b''.join(rows)


def text(src, rel, fix=None):
    t = rd(src).decode('cp866').replace('\x1a', '').replace('\r\n', '\n')
    if fix:
        t = fix(t)
    wr(rel, t.encode('utf-8'))


def main():
    # ---- pictures
    for n in 'xearth xweapon xbutton xsign xparam xkey xlabel xscan'.split():
        png(os.path.join(A, 'IMAGES', n.upper() + '.TIF'), f'gfx/ui/{n}.png')
    png(os.path.join(A, 'IMAGES', 'XHERO.TIF'), 'gfx/sprites/xhero.png')
    png(os.path.join(A, 'IMAGES', 'XMARKER.TIF'), 'gfx/sprites/xmarker.png')
    for n in range(21):
        png(os.path.join(A, 'IMAGES', f'XM{n}.TIF'), f'gfx/land/xm{n}.png')
    shutil.copy(os.path.join(OUT, 'gfx/land/xm11.png'), os.path.join(OUT, 'gfx/land/xm11_archive.png'))
    png_from_rows(unmask(rd(R2, 'xm11.unp')[192:], 5, 16, 32), 32, 'gfx/land/xm11.png')
    for n in range(1, 61):
        png(os.path.join(A, 'IMAGES', f'X{n}.TIF'), f'gfx/pedia/x{n}.png')
    up6 = rd(R2, 'xup6.unp')
    for k, n in enumerate((16, 10, 9)):
        shutil.copy(os.path.join(OUT, f'gfx/pedia/x{n}.png'), os.path.join(OUT, f'gfx/pedia/x{n}_archive.png'))
        png_from_rows(up6[k * 5376:(k + 1) * 5376], 28, f'gfx/pedia/x{n}.png')
    for pre, cnt in (('xd', 24), ('xs', 56), ('xx', 56), ('xt', 28)):
        for n in range(1, cnt + 1):
            png(os.path.join(A, 'XDEMO', f'{pre.upper()}{n}.TIF'), f'gfx/intro/{pre}{n}.png')
    png(os.path.join(A, 'XDEMO', 'XTITLE.TIF'), 'gfx/intro/xtitle.png')
    for n in 'xdisk2 xend1 xpanic xtitle xnakl xn1 xn2 xn3 xn4 xn5'.split():       # source art of full screens
        png(os.path.join(A, 'IMAGES', n.upper() + '.TIF'), f'gfx/art/{n}.png')

    # ---- screens (.scr, 6912 bytes)
    for n in 'xhist xi1 xi2 xi3 xi4'.split():
        wr(f'screens/{n}.scr', rd(A, 'IMAGES', n.upper() + '.SCR'))
    man0, man1 = rd(R1, 'XBINSTR.LP0.unp'), rd(R1, 'XBINSTR.LP1.unp')
    blobs = {}
    p = 0
    for n in ('xn3', 'xn2', 'xn4'):
        ln = struct.unpack_from('<H', man0, p)[0] + 2
        blobs[n] = lpc.unpack(man0[p:p + ln])
        p += ln
    p += 300 + 21
    blobs['xn5'] = lpc.unpack(man0[p:])
    k = man1.index(b'   STACK STACK STACK STACK ') + 27
    blobs['xn1'] = lpc.unpack(man1[k:])
    for n, b in blobs.items():
        assert b[:8] == b'fromIBM ' and len(b) == 6929, n
        wr(f'screens/{n}.scr', b[17:])
    end = rd(R2, 'xend.unp')
    mus, scr, txt = struct.unpack_from('<3H', end, 0x3000)
    wr('screens/xend1.scr', end[scr - 0xC000:txt - 0xC000])
    wr('music/xend.mus', end[:scr - 0xC000])

    # ---- maps, tables, fonts, music
    for f in os.listdir(os.path.join(A, 'XMAP')):
        wr('maps/' + f.lower(), rd(A, 'XMAP', f))
    wr('maps/xl18_archive.lnd', rd(A, 'XMAP', 'XL18.LND'))
    wr('maps/xl18.lnd', rd(R2, 'xl18.unp'))
    wr('tables/xangles.bin', rd(A, 'XLESHA', 'ANGLES.BIN'))
    wr('tables/xscales.bin', rd(A, 'XLESHA', 'SCALES.BIN'))
    gfxconv.tiles_from_cpp(os.path.join(A, 'CPP', 'XBLOX.CPP'), os.path.join(OUT, 'tiles.txt'))
    main_img = rd(R1, 'XCOM3.PG5.unp')
    wr('fonts/xfont.bin', main_img[0xC00:0xC00 + 928])
    wr('fonts/xnf1.fon', rd(A, 'DATA', 'XNF1.FON'))
    wr('fonts/xnf2.fon', rd(A, 'DATA', 'XNF2.FON'))
    title = rd(R1, 'DANGEROU.LPC.unp')
    k = title.index(b'  UFO-2 Beginning')
    # the blocks of the title program: XI4, XI1, M_UFO, XI2, XI3 (all packed) start after the interrupt handler
    p = 0x728C - 0x7000
    for n in ('xi4', 'xi1', 'm_ufo'):
        ln = struct.unpack_from('<H', title, p)[0] + 2
        if n == 'm_ufo':
            wr('music/m_ufo.bin', lpc.unpack(title[p:p + ln]))
        p += ln
    intro = rd(R1, 'XBEGIN.LPC.unp')
    k = intro.index(b'M_IVAN2 C')
    wr('music/m_ivan2.bin', intro[k:k + 9489])
    for f in os.listdir(os.path.join(A, 'MUSIC')):
        wr('music/src/' + f, rd(A, 'MUSIC', f))

    # ---- texts
    for n in 'xname xmenu xfopedia xend xinstr'.split():
        text(os.path.join(A, 'DATA', n.upper() + '.TXT'), f'text/ru/{n}.txt')
    text(os.path.join(A, 'DATA', 'XWORD.TXT'), 'text/ru/xword_archive.txt')
    text(os.path.join(A, 'DATA', 'XWORD.TXT'), 'text/ru/xword.txt',
         fix=lambda t: t.replace('Перемещения врагов#', 'Перемещения врагов').replace('Перемещения врагов \n', 'Перемещения врагов\n'))
    print('assets/ written')


if __name__ == '__main__':
    main()
