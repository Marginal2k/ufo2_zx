"""Hobeta (TR-DOS file container) reader/writer.

Layout of a .$x file (17-byte header + data padded to a multiple of 256):

    0..7   file name (space padded)
    8      type letter (B, C, D, #, or anything else)
    9..10  start address (or BASIC program length)
    11..12 length in bytes
    13     always 0
    14     length in 256-byte sectors
    15..16 header checksum:  (sum of bytes 0..14 * 257 + 105) & 0xFFFF
"""
import struct
from dataclasses import dataclass


@dataclass
class HobetaFile:
    name: str          # 8 chars, cp866-decoded, right-stripped
    ftype: str         # one character
    start: int
    length: int
    data: bytes        # exactly `length` bytes (padding removed)
    checksum_ok: bool = True


def checksum(header15: bytes) -> int:
    return (sum(header15) * 257 + 105) & 0xFFFF


def read(path) -> HobetaFile:
    raw = open(path, 'rb').read()
    if len(raw) < 17:
        raise ValueError(f'{path}: too short for a Hobeta file')
    start, length = struct.unpack_from('<HH', raw, 9)
    chk = struct.unpack_from('<H', raw, 15)[0]
    return HobetaFile(
        name=raw[:8].decode('cp866', 'replace').rstrip(),
        ftype=chr(raw[8]),
        start=start,
        length=length,
        data=raw[17:17 + length],
        checksum_ok=(chk == checksum(raw[:15])),
    )


def write(path, name: str, ftype: str, start: int, data: bytes):
    sectors = (len(data) + 255) // 256
    hdr = bytearray(name.encode('cp866')[:8].ljust(8, b' '))
    hdr += ftype.encode('ascii')
    hdr += struct.pack('<HH', start, len(data)) + bytes([0, sectors])
    hdr += struct.pack('<H', checksum(bytes(hdr)))
    pad = (-len(data)) % 256
    with open(path, 'wb') as f:
        f.write(hdr + data + bytes(pad))
