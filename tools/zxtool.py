#!/usr/bin/env python3
"""Small ZX Spectrum file utilities (platform independent).

    zxtool.py info   FILE.$C            show Hobeta header
    zxtool.py unpack FILE.$C [OUT.bin]  strip the Hobeta header
    zxtool.py pack   IN.bin NAME TYPE START OUT.$C
    zxtool.py basic  FILE.$B            print a tokenized BASIC program as text
    zxtool.py scr    FILE.bin OUT.png   render a 6912-byte screen (needs Pillow)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hobeta  # noqa: E402

TOKENS = ('RND INKEY$ PI FN POINT SCREEN$ ATTR AT TAB VAL$ CODE VAL LEN SIN COS TAN ASN ACS ATN LN EXP INT '
          'SQR SGN ABS PEEK IN USR STR$ CHR$ NOT BIN OR AND <= >= <> LINE THEN TO STEP DEF_FN CAT FORMAT MOVE '
          'ERASE OPEN# CLOSE# MERGE VERIFY BEEP CIRCLE INK PAPER FLASH BRIGHT INVERSE OVER OUT LPRINT LLIST '
          'STOP READ DATA RESTORE NEW BORDER CONTINUE DIM REM FOR GO_TO GO_SUB INPUT LOAD LIST LET PAUSE NEXT '
          'POKE PRINT PLOT RUN SAVE RANDOMIZE IF CLS DRAW CLEAR RETURN COPY').split()
assert len(TOKENS) == 91
TOKENS = [t.replace('_', ' ') for t in TOKENS]


def detok_basic(data: bytes, prog_len=None):
    """Yield 'NNNN text' lines. Stops at the variables area."""
    i, end = 0, len(data) if prog_len is None else prog_len
    while i + 4 <= end:
        num = (data[i] << 8) | data[i + 1]            # line numbers are big-endian
        ln = data[i + 2] | data[i + 3] << 8
        body = data[i + 4:i + 4 + ln]
        i += 4 + ln
        out, k, quote = [], 0, False
        while k < len(body):
            c = body[k]
            if c == 0x0D:
                break
            if c == 0x0E:                              # hidden 5-byte number
                k += 6
                continue
            if c == ord('"'):
                quote = not quote
            if c >= 0xA5 and not quote:
                tok = TOKENS[c - 0xA5]
                out.append(f' {tok} ' if len(tok) > 1 else tok)
            elif c >= 0x80 and not quote or c < 0x20:
                out.append(f'{{{c}}}')
            elif c >= 0x80:
                out.append(f'{{{c}}}')
            else:
                out.append(chr(c))
            k += 1
        yield f'{num:4d} ' + ''.join(out).replace('  ', ' ').strip()


def main(a):
    if len(a) < 2:
        print(__doc__)
        return 1
    cmd = a[0]
    if cmd == 'info':
        h = hobeta.read(a[1])
        print(f'name={h.name!r} type={h.ftype!r} start={h.start} length={h.length} checksum_ok={h.checksum_ok}')
    elif cmd == 'unpack':
        h = hobeta.read(a[1])
        out = a[2] if len(a) > 2 else os.path.splitext(a[1])[0] + '.bin'
        open(out, 'wb').write(h.data)
    elif cmd == 'pack':
        hobeta.write(a[5], a[2], a[3], int(a[4]), open(a[1], 'rb').read())
    elif cmd == 'basic':
        h = hobeta.read(a[1])
        print('\n'.join(detok_basic(h.data, h.start if h.start <= h.length else None)))
    elif cmd == 'scr':
        from PIL import Image
        d = open(a[1], 'rb').read()
        pal = [(0, 0, 0), (0, 0, 205), (205, 0, 0), (205, 0, 205), (0, 205, 0), (0, 205, 205), (205, 205, 0), (205, 205, 205)]
        img = Image.new('RGB', (256, 192))
        for y in range(192):
            row = ((y & 7) << 8) | (((y >> 3) & 7) << 5) | ((y >> 6) << 11)
            for xb in range(32):
                b = d[row + xb]
                at = d[6144 + (y >> 3) * 32 + xb] if len(d) >= 6912 else 7
                br = 1.2 if at & 64 else 1.0
                ink, pap = at & 7, (at >> 3) & 7
                for bit in range(8):
                    c = pal[ink if b & (0x80 >> bit) else pap]
                    img.putpixel((xb * 8 + bit, y), tuple(min(255, int(v * br)) for v in c))
        img.save(a[2])
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
