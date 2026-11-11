#!/usr/bin/env python3
"""Graphics converters of UFO-2: ports of the 1996 Turbo Pascal / Borland C++ tools
(XSPRITER.PAS, XHERO.PAS, XLAND.PAS, XUP.PAS, XDEMO*.PAS, XBLOX.CPP).

Pictures are 1-bit images (the author's TIFs or PNGs): black pixel = ink (bit 1 on the Spectrum).
"""
import os
import re

from PIL import Image


def bitmap(path):
    """-> (bytes per row, list of rows), ink = 1."""
    im = Image.open(path).convert('1')
    w, h = im.size
    wb = (w + 7) // 8
    raw = im.tobytes()
    return wb, [bytes(b ^ 255 for b in raw[y * wb:(y + 1) * wb]) for y in range(h)]


def plain(path, wbytes, rows):
    """Rows of the picture as they are (XSPRITER, XUP, XDEMO*: x bytes by rows lines)."""
    wb, r = bitmap(path)
    assert wb >= wbytes and len(r) >= rows, (path, wb, len(r), wbytes, rows)
    return b''.join(row[:wbytes] for row in r[:rows])


def masked(path, bands, per_band, lines):
    """Sprites 2 bytes wide with a mask (XHERO: 24 lines, XLAND: 32 lines).

    The picture is made of bands 2*lines high: the upper half of a band holds the images, the lower half the masks,
    16 sprites side by side. Output per sprite, per line, per byte: mask, image XOR mask.
    """
    wb, r = bitmap(path)
    out = bytearray()
    for i in range(bands):
        for j in range(per_band):
            for k in range(lines):
                for m in range(2):
                    bb = r[i * 2 * lines + k + lines][j * 2 + m]
                    aa = r[i * 2 * lines + k][j * 2 + m] ^ bb
                    out += bytes([bb, aa])
    return bytes(out)


# ---- XBLOX.CPP: properties of landscape tiles ---------------------------------------------------------
TYPES = '.D`/LGFE'
FTYP = [1, 3, 2, 2, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 2, 2, 2, 2, 2, 2, 2]     # 16-tile rows in landscape set xm0..xm20


def read_tiles(path):
    """assets/tiles.txt -> (list of 16-byte attribute rows, list of 16-byte conversion rows), 72 rows each."""
    attrs, convs = [], []
    block = []
    for ln in open(path, encoding='utf-8'):
        ln = ln.split('#')[0].rstrip()
        if not ln.strip():
            continue
        block.append(ln.strip())
        if len(block) == 6:
            s, b, m, t, f, c = block
            block = []
            row = bytearray()
            for j in range(16):
                assert s[j] in 'S.' and b[j] in 'B.' and m[j] in 'M.' and f[j] in '0123', block
                row.append((128 if s[j] == 'S' else 0) + (64 if b[j] == 'B' else 0) + (32 if m[j] == 'M' else 0)
                           + (TYPES.index(t[j]) << 2) + int(f[j]))
            attrs.append(bytes(row))
            cv = [255 if x in ('--', '..') else int(x) for x in c.split()]
            assert len(cv) == 16, c
            convs.append(bytes(cv))
    assert len(attrs) == sum(FTYP), len(attrs)
    return attrs, convs


def tile_tables(attrs, convs, n):
    """96 bytes of attributes + 96 bytes of conversion for landscape set n (2..20), as XBLOX.CPP builds them.

    The arrays are static in the C program, so entries not written for a set keep the values of the previous ones.
    """
    xa, xc = bytearray(128), bytearray(128)

    def copy(bnk, ln, pos):
        for k in range(bnk, bnk + ln):
            xa[pos:pos + 16] = attrs[k]
            xc[pos:pos + 16] = convs[k]
            pos += 16

    copy(0, 1, 0)
    bnk = 4
    for i in range(2, n + 1):
        if FTYP[i] == 2:
            copy(1, 3, 16)
            copy(bnk, 2, 64)
        else:
            copy(bnk, 5, 16)
        bnk += FTYP[i]
    return bytes(xa[:96]), bytes(xc[:96])


def tiles_from_cpp(cpp_path, out_path):
    """One-off: assets/tiles.txt from the tables of XBLOX.CPP."""
    t = open(cpp_path, 'rb').read().decode('cp866')
    rows = re.findall(r'\{\s*"(.{16})",\s*"(.{16})",\s*"(.{16})",\s*"(.{16})",\s*"(.{16})"\s*\}', t)
    cn = t[t.index('char xcnv'):t.index('char ftyp')]
    convs = [re.findall(r'nn|\d+', x) for x in re.findall(r'\{([^{}]*)\}', cn)]
    assert len(rows) == len(convs) == sum(FTYP), (len(rows), len(convs))
    names = []
    for i, n in enumerate(FTYP):
        names += [f'xm{i} row {k + 1}' for k in range(n)]
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('''# Properties of the landscape tiles of UFO-2 (from XBLOX.CPP, 1996). One block per row of 16 tiles:
#   line 1  S = blocks the view            line 2  B = stops bullets          line 3  M = cannot be walked through
#   line 4  object type: . none, D door, ` and / , L , G , F , E  (codes 0..7 in this order: . D ` / L G F E)
#   line 5  0..3 = how the tile takes damage
#   line 6  the tile it turns into when destroyed (number, -- = stays itself)
''')
        for name, r, c in zip(names, rows, convs):
            f.write(f'\n# {name}\n' + '\n'.join(r) + '\n' + ' '.join('--' if x == 'nn' else f'{int(x):2}' for x in c) + '\n')
