#!/usr/bin/env python3
"""Reader for FDI disk images (UKV format): gives sectors by (cylinder, head, sector id)."""
import struct


class Fdi:
    def __init__(self, path):
        d = open(path, 'rb').read()
        assert d[:3] == b'FDI', 'not an FDI image'
        self.cyls, self.heads, text, data, extra = struct.unpack_from('<HHHHH', d, 4)
        self.tracks = {}            # (cyl, head) -> list of dict(c,h,r,n,flags,data)
        p = 14 + extra
        for c in range(self.cyls):
            for h in range(self.heads):
                toff, _, nsec = struct.unpack_from('<IHB', d, p)
                p += 7
                secs = []
                for _ in range(nsec):
                    sc, sh, sr, sn, fl, soff = struct.unpack_from('<BBBBBH', d, p)
                    p += 7
                    size = 128 << sn
                    o = data + toff + soff
                    secs.append(dict(c=sc, h=sh, r=sr, n=sn, flags=fl, data=d[o:o + size]))
                self.tracks[(c, h)] = secs

    def sector(self, cyl, head, r):
        for s in self.tracks[(cyl, head)]:
            if s['r'] == r:
                return s['data']
        raise KeyError((cyl, head, r))

    def describe(self):
        out = []
        for (c, h), secs in sorted(self.tracks.items()):
            out.append(f'{c:2}/{h}: ' + ' '.join(f"{s['r']:02X}:{128 << s['n']}{'' if s['flags'] & 0x1F else '!'}" for s in secs))
        return '\n'.join(out)


if __name__ == '__main__':
    import sys
    print(Fdi(sys.argv[1]).describe())
