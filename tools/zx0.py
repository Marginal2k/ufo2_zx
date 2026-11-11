#!/usr/bin/env python3
"""ZX0 (Einar Saukas, format v2) for UFO-2: every packed block of the game is

    word N, then N bytes of a ZX0 stream

(the length word is what the 1996 packer "LPC" also put in front; the game skips it or uses it to move a block).
Packing: the console compressor tools/bin/zx0.exe (or %ZX0%, or zx0 in PATH); without it the slow Python port in
tools/third_party/zx0. Unpacking here is a port of the Z80 decoder (src/lib/dzx0.asm) and is used to check
every packed block and to see whether a block can be unpacked "in place".

    python tools/zx0.py c in.bin out.zx0      python tools/zx0.py d in.zx0 out.bin
"""
import os
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_exe():
    for c in (os.environ.get('ZX0'), os.path.join(ROOT, 'tools', 'bin', 'zx0.exe'), os.path.join(ROOT, 'tools', 'bin', 'zx0')):
        if c and os.path.isfile(c):
            return c
    return shutil.which('zx0')


def compress_stream(data):
    exe = find_exe()
    if exe:
        with tempfile.TemporaryDirectory() as d:
            src, dst = os.path.join(d, 'in.bin'), os.path.join(d, 'out.zx0')
            with open(src, 'wb') as f:
                f.write(data)
            r = subprocess.run([exe, '-f', src, dst], capture_output=True, text=True)
            if r.returncode or not os.path.exists(dst):
                raise RuntimeError(f'{exe} failed: {r.stdout}{r.stderr}')
            with open(dst, 'rb') as f:
                return f.read()
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'third_party'))
    from zx0 import zx0_compress
    z = zx0_compress(bytearray(data))
    return bytes(z[0]) if isinstance(z, tuple) else bytes(z)


def unpack_stream(s, trace=None):
    """Port of dzx0_standard. trace (a list) receives (bytes read, bytes written) after every step."""
    out = bytearray()
    p = 0
    a = 0x80
    offset = 1

    def elias(bc, backtrack=False):
        nonlocal a, p
        while True:
            if not backtrack:
                a <<= 1
                cy = a >> 8
                a &= 255
                if a == 0:
                    a = (s[p] << 1) | cy
                    p += 1
                    cy = a >> 8
                    a &= 255
                if cy:
                    return bc
            backtrack = False
            a <<= 1
            bc = ((bc << 1) | (a >> 8)) & 0xFFFF
            a &= 255

    def flag():
        nonlocal a
        a <<= 1
        cy = a >> 8
        a &= 255
        return cy

    state = 'lit'
    while True:
        if state == 'lit':
            n = elias(1)
            out += s[p:p + n]
            p += n
            if trace is not None:
                trace.append((p, len(out)))
            if flag():
                state = 'new'
            else:
                n = elias(1)
                state = 'copy'
        if state == 'new':
            c = elias(0xFE) & 255
            c = (c + 1) & 255
            if c == 0:
                break
            lsb = s[p]
            p += 1
            # RR B / RR C: a 16-bit shift right; the carry (set by the Elias code) comes in as bit 15, so the
            # value is the negative offset; the bit shifted out is the first bit of the length
            cy = lsb & 1
            neg = 0x8000 | (((c << 8) | lsb) >> 1)
            offset = 0x10000 - neg
            n = 1 if cy else elias(1, backtrack=True)
            n += 1
            state = 'copy'
        if state == 'copy':
            for _ in range(n):
                out.append(out[-offset])
            if trace is not None:
                trace.append((p, len(out)))
            state = 'new' if flag() else 'lit'
    return bytes(out), p


def pack(data):
    s = compress_stream(data)
    back, used = unpack_stream(s)
    assert back == data and used == len(s), 'ZX0 round trip failed'
    return struct.pack('<H', len(s)) + s


def unpack(f):
    n = struct.unpack_from('<H', f)[0]
    return unpack_stream(f[2:2 + n])[0]


def inplace_margin(packed, gap):
    """A packed block (with its length word) whose LAST byte lies `gap` bytes behind the end of the unpacked data
    is unpacked over itself. Returns the smallest distance between the read and the write position (>= 0 = safe)."""
    n = struct.unpack_from('<H', packed)[0]
    s = packed[2:2 + n]
    tr = []
    out, _ = unpack_stream(s, tr)
    start = len(out) + gap - n             # where the stream starts, relative to the start of the output
    # before a step the bytes it reads must not have been overwritten: compare with the previous write position
    worst = 1 << 30
    prev_w = 0
    for r, w in tr:
        worst = min(worst, start + r - w)
        prev_w = w
    return worst


if __name__ == '__main__':
    mode, a, b = sys.argv[1:4]
    src = open(a, 'rb').read()
    open(b, 'wb').write(unpack(src) if mode == 'd' else pack(src))
