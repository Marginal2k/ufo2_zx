import sys
from PIL import Image
name, shots = sys.argv[1], sys.argv[2].split(',')
ims = [Image.open(f'build/emu/{name}_{n}.png') for n in shots]
w = Image.new('RGB', (sum(i.width for i in ims), ims[0].height))
x = 0
for i in ims:
    w.paste(i, (x, 0)); x += i.width
w.save(f'build/emu/{name}.png')
