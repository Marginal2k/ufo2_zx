#!/usr/bin/env python3
"""LPC - the compression used by UFO-2 (packer XLPC.EXE of 1996, its source is lost; the unpacker is DELPC in the game).

File:   word N, then N bytes of stream.
Stream: 4 bytes = the LAST four bytes of the unpacked data, then tokens up to the end mark #80:
  0lllnnno oooooooo            copy n+3 bytes (3..10) from distance o (9 bits, 1..511), then l (0..7) literals
  10llllll                     l literals (1..63); l = 0 is the end mark
  11nnnnnn lllloooo oooooooo   copy n+4 bytes (4..67) from distance o (12 bits, 1..4095), then l (0..15) literals
Literals are stored rotated left by one bit (the unpacker does RRCA).
A copy may overlap its own output (distance < length), as with LDIR.

    python tools/lpc.py d in.lpc out.bin      python tools/lpc.py c in.bin out.lpc
"""
import struct
import sys


def rol(b):
    return ((b << 1) | (b >> 7)) & 255


def ror(b):
    return ((b >> 1) | (b << 7)) & 255


def unpack_stream(s, pos=0):
    """Returns (data, position after the end mark)."""
    tail = s[pos:pos + 4]
    p = pos + 4
    out = bytearray()
    while True:
        a = s[p]
        if a < 0x80:
            dist, n, nl = ((a & 1) << 8) | s[p + 1], ((a >> 1) & 7) + 3, a >> 4
            p += 2
        elif a < 0xC0:
            p += 1
            if a == 0x80:
                break
            dist, n, nl = 0, 0, a & 0x3F
        else:
            b = s[p + 1]
            dist, n, nl = ((b & 15) << 8) | s[p + 2], (a & 0x3F) + 4, b >> 4
            p += 3
        for _ in range(n):
            out.append(out[-dist])
        out.extend(ror(b) for b in s[p:p + nl])
        p += nl
    out += tail
    return bytes(out), p


def unpack(f):
    n = struct.unpack_from('<H', f)[0]
    return unpack_stream(f[2:2 + n])[0]


def pack_stream(data):
    """Shortest stream for the longest matches found, by dynamic programming over token starts."""
    assert len(data) >= 4
    body, tail = data[:-4], data[-4:]
    n = len(body)
    best_s = [(0, 0)] * (n + 1)     # (length, distance): distance <= 511, length <= 10
    best_l = [(0, 0)] * (n + 1)     # distance <= 4095, length <= 67
    heads = {}
    prev = [-1] * n
    for i in range(n - 2):
        key = body[i:i + 3]
        j = heads.get(key, -1)
        bs = bl = (0, 0)
        tries = 0
        lim = min(67, n - i)
        while j >= 0 and i - j <= 4095 and tries < 300:
            d = i - j
            m = 0
            while m < lim and body[j + m] == body[i + m]:
                m += 1
            if m > bl[0]:
                bl = (m, d)
            if d <= 511 and min(m, 10) > bs[0]:
                bs = (min(m, 10), d)
            if bl[0] >= lim:
                break
            j = prev[j]
            tries += 1
        best_s[i], best_l[i] = bs, bl
        prev[i] = heads.get(key, -1)
        heads[key] = i
    INF = 1 << 60
    cost = [INF] * (n + 1)          # cheapest size of the stream for body[i:] when a token starts at i
    choice = [None] * (n + 1)
    cost[n] = 0
    for i in range(n - 1, -1, -1):
        c, ch = INF, None
        for l in range(1, min(63, n - i) + 1):
            v = 1 + l + cost[i + l]
            if v < c:
                c, ch = v, ('L', 0, 0, l)
        m, d = best_s[i]
        for ln in range(3, m + 1):
            for l in range(0, min(7, n - i - ln) + 1):
                v = 2 + l + cost[i + ln + l]
                if v < c:
                    c, ch = v, ('S', ln, d, l)
        m, d = best_l[i]
        if m >= 4:
            for ln in (range(4, m + 1) if m <= 12 else (m, m - 1, m - 2, m - 3, 11, 4)):
                for l in range(0, min(15, n - i - ln) + 1):
                    v = 3 + l + cost[i + ln + l]
                    if v < c:
                        c, ch = v, ('M', ln, d, l)
        cost[i], choice[i] = c, ch
    out = bytearray(tail)
    i = 0
    while i < n:
        kind, ln, d, l = choice[i]
        if kind == 'L':
            out.append(0x80 | l)
        elif kind == 'S':
            out += bytes([(l << 4) | ((ln - 3) << 1) | (d >> 8), d & 255])
        else:
            out += bytes([0xC0 | (ln - 4), (l << 4) | (d >> 8), d & 255])
        i += ln
        out += bytes(rol(b) for b in body[i:i + l])
        i += l
    out.append(0x80)
    return bytes(out)


def pack(data):
    s = pack_stream(data)
    assert unpack_stream(s)[0] == data
    return struct.pack('<H', len(s)) + s


if __name__ == '__main__':
    mode, a, b = sys.argv[1:4]
    src = open(a, 'rb').read()
    open(b, 'wb').write(unpack(src) if mode == 'd' else pack(src))


def inplace_margin(packed, area):
    """Unpacking in place (DELPCX): the packed file is moved to the end of an area of `area` bytes and unpacked
    to its start. Returns the smallest distance between the read and the write pointers (must be >= 0)."""
    n = struct.unpack_from('<H', packed)[0]
    s = packed[2:2 + n]
    r0 = area - n               # where the stream starts after the move
    p, w, worst = 4, 0, 1 << 30
    while True:
        a = s[p]
        if a < 0x80:
            cnt, nl = ((a >> 1) & 7) + 3, a >> 4
            p += 2
        elif a < 0xC0:
            p += 1
            if a == 0x80:
                break
            cnt, nl = 0, a & 0x3F
        else:
            cnt, nl = (a & 0x3F) + 4, s[p + 1] >> 4
            p += 3
        w += cnt
        worst = min(worst, r0 + p - w)      # the token after the copy must not be overwritten yet
        w += nl
        p += nl
        worst = min(worst, r0 + p - w)
    return worst
