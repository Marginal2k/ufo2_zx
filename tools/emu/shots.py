#!/usr/bin/env python3
"""Turn the `shots` of a result file (build/emu/<name>.json: {name: [6912 bytes of a ZX screen]}) into PNGs.

    python tools/emu/shots.py mouse            # -> build/emu/mouse_<shot>.png
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import zxtool  # noqa: E402

name = sys.argv[1]
out = os.path.join(ROOT, 'build', 'emu')
data = json.load(open(os.path.join(out, name + '.json'), encoding='utf-8'))
data = data.get('data', data)
for shot, scr in data.get('shots', {}).items():
    raw = os.path.join(out, 'scr_tmp.bin')
    open(raw, 'wb').write(bytes(scr))
    png = os.path.join(out, f'{name}_{shot}.png')
    zxtool.main(['scr', raw, png])
    print(png)
