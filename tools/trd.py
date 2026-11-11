#!/usr/bin/env python3
"""Minimal TR-DOS disk (.trd) writer + tokenized BASIC helper.

    from trd import Trd, basic_program
    d = Trd(label='UFO')
    d.add_file('boot', 'B', basic_program(...), start=10)       # BASIC with autostart line 10
    d.add_file('code', 'C', data, start=32768)                   # CODE file
    d.add_raw(sector_count)                                      # reserve/fill sectors, returns (track, sector)
    d.save('x.trd')

Disk: 80 cylinders, 2 sides, 16 sectors of 256 bytes (655360 bytes); catalog in track 0
sectors 0-7, system sector = track 0 sector 8 (the "sector 9" of the TR-DOS documentation).
"""
import struct

SEC = 256
SPT = 16


class Trd:
    def __init__(self, label='NEWDISK', tracks=160):
        self.img = bytearray(tracks * SPT * SEC)
        self.tracks = tracks
        self.files = []
        self.next = 16                     # first free logical sector (track 1, sector 0)
        self.label = label

    def alloc(self, nsec):
        s = self.next
        if (s + nsec) * SEC > len(self.img):
            raise ValueError('disk full')
        self.next += nsec
        return s

    def add_raw(self, data):
        """Place data at the next free sectors; returns (logical sector, sector count)."""
        n = (len(data) + SEC - 1) // SEC
        s = self.alloc(n)
        self.img[s * SEC:s * SEC + len(data)] = data
        return s, n

    def add_file(self, name, ftype, data, start=0, length=None):
        if len(self.files) >= 128:
            raise ValueError('catalog full')
        s, n = self.add_raw(data)
        if length is None:
            length = len(data)
        nm = name.encode('ascii')[:8].ljust(8, b' ')
        ent = nm + ftype.encode('ascii') + struct.pack('<HH', start, length) + bytes([n, s % SPT, s // SPT])
        self.files.append(ent)
        return s

    def finish(self):
        cat = b''.join(self.files)
        self.img[0:len(cat)] = cat
        sysx = 8 * SEC
        sysb = bytearray(SEC)
        nxt = self.next
        sysb[0xE1] = nxt % SPT
        sysb[0xE2] = nxt // SPT
        sysb[0xE3] = 0x16                       # 80 tracks, double sided
        sysb[0xE4] = len(self.files)
        struct.pack_into('<H', sysb, 0xE5, self.tracks * SPT - nxt)
        sysb[0xE7] = 0x10                       # TR-DOS id
        sysb[0xF5:0xFD] = self.label.encode('ascii')[:8].ljust(8, b' ')
        self.img[sysx:sysx + SEC] = sysb
        return bytes(self.img)

    def save(self, path):
        open(path, 'wb').write(self.finish())


# --- tokenized BASIC -------------------------------------------------------------
KW = {'RANDOMIZE': 0xF9, 'USR': 0xC0, 'REM': 0xEA, 'LOAD': 0xEF, 'CODE': 0xAF, 'CLEAR': 0xFD, 'VAL': 0xB0,
      'PRINT': 0xF5, 'POKE': 0xF4, 'PAPER': 0xDA, 'BORDER': 0xE7, 'INK': 0xD9, 'PAUSE': 0xF2, 'RUN': 0xF7,
      'GO TO': 0xEC, 'LET': 0xF1, 'IF': 0xFA, 'THEN': 0xCB, 'OUT': 0xDF, 'CLS': 0xFB}


def basic_line(num, text):
    """Tokenize one line: keywords in upper case separated by spaces; "…" strings and digits kept literal.
    Numbers must be written as VAL "n" (hidden 5-byte forms are not generated)."""
    out = bytearray()
    i = 0
    keys = sorted(KW, key=len, reverse=True)
    while i < len(text):
        if text[i] == '"':
            j = text.index('"', i + 1)
            out += text[i:j + 1].encode('cp866')
            i = j + 1
            continue
        for k in keys:
            if text.startswith(k, i) and not (text[i + len(k):i + len(k) + 1].isalpha() and k.isalpha() and False):
                out.append(KW[k])
                i += len(k)
                break
        else:
            if text[i] != ' ':
                out += text[i].encode('cp866')
            i += 1
    out.append(0x0D)
    return struct.pack('>H', num) + struct.pack('<H', len(out)) + bytes(out)


def basic_program(lines):
    return b''.join(basic_line(n, t) for n, t in lines)
