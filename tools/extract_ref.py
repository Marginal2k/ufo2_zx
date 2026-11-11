#!/usr/bin/env python3
"""Extract the blocks of the two original 1996 disks (FDI images) into reference/disk1, reference/disk2.

Layout as written by CPP/DISKMAKE.CPP: disk 1 - 512-byte sectors #F5..#FD from track 1, files on sector bounds,
table F_DAT in the loader (track 0, sector 9); disk 2 - 1024-byte sectors #F4..#F8 from track 4, files on 4-byte bounds.
"""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from fdi import Fdi
import lpc

REF = os.path.join(ROOT, 'reference')
N1 = ["DANGEROU.LPC", "XBINSTR.LP0", "XBINSTR.LP1", "XCOM3.PG7", "XCOM3.PG0", "XCOM3.PG1", "XCOM3.PG3", "XCOM3.PG4",
      "XCOM3.PG5", "XCOM3.PG2", None, None, None, "XDEMO0.LPC", "XDEMO1.LPC", "XDEMO2.LPC", "XDEMOS6.LPC",
      "XDEMOS7.LPC", "XDEMOTXT.LPC", "XBEGIN.LPC"]
N2 = ("m2 m3 m4 m5 m10 m7 m8 m9 m6 m11 m12 m13 m14 m15 m16 m17 m18 m19 m20 l2 end l3 l4 l5a l5b l5c l5d l6a l6b l6c "
      "l6d X2 l7 l8a l8b l8c l8d l9 X3 l10a l10b l10c l10d l11 l12 l13 l14 l15 l19 l17 l18 l16 l20 "
      + ' '.join(f'up{i}' for i in range(1, 21))).split()


def main():
    d1 = Fdi(os.path.join(REF, 'ufo2_disk1.fdi'))
    o1 = os.path.join(REF, 'disk1')
    os.makedirs(o1, exist_ok=True)
    boot = d1.sector(0, 0, 9)
    open(os.path.join(o1, 'xbstart.bin'), 'wb').write(boot)
    # F_DAT is right after MEMS: OR %10000 / PUSH BC / LD BC,#7FFD / OUT (C),A / POP BC / RET
    k = boot.index(bytes.fromhex('f610c501fd7fed79c1c9')) + 10
    lin = b''.join(d1.sector(t, 0, r) for t in range(1, 78) if d1.tracks[(t, 0)] for r in range(0xF5, 0xFE))
    for i, name in enumerate(N1):
        sec, trk, ln = boot[k + i * 3:k + i * 3 + 3]
        if not name:
            continue
        off = ((trk - 1) * 9 + sec - 0xF5) * 512
        raw = lin[off:off + ln * 512]
        open(os.path.join(o1, name), 'wb').write(raw)
        if name != 'XCOM3.PG0':
            un = lpc.unpack(raw)
            open(os.path.join(o1, name + '.unp'), 'wb').write(un)
            print(f'disk1 {i + 1:2} {name:13} trk {trk:2} sec {sec:02X} {ln * 512:6} -> {len(un)}')
        else:
            print(f'disk1 {i + 1:2} {name:13} trk {trk:2} sec {sec:02X} {ln * 512:6} (not packed)')

    d2 = Fdi(os.path.join(REF, 'ufo2_disk2.fdi'))
    o2 = os.path.join(REF, 'disk2')
    os.makedirs(o2, exist_ok=True)
    open(os.path.join(o2, 'xbstart2.bin'), 'wb').write(d2.sector(0, 0, 9))
    lin = b''.join(d2.sector(t, 0, r) for t in range(4, 78) if d2.tracks[(t, 0)] for r in range(0xF4, 0xF9))
    open(os.path.join(o2, 'disk.bin'), 'wb').write(lin)
    pos = 0
    for i, name in enumerate(N2):
        n = struct.unpack_from('<H', lin, pos)[0]
        raw = lin[pos:pos + n + 2]
        un = lpc.unpack(raw)
        open(os.path.join(o2, f'x{name}.lpc'), 'wb').write(raw)
        open(os.path.join(o2, f'x{name}.unp'), 'wb').write(un)
        print(f'disk2 {i + 1:2} x{name:5} sec {pos // 1024:3} shift {pos % 1024 // 4:3} len {n + 2:5} -> {len(un)}')
        pos += (n + 2 + 3) & ~3


if __name__ == '__main__':
    main()
