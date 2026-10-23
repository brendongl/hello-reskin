#!/usr/bin/env python3
"""Pikachu recipe extras: the 'used block' (empty gift box), the ? menu glyph (gift icon) and its frame.
Run after fit.py has written packs/pikachu/textures/FaceEventHatenaBlock00.png."""
import glob
import numpy as np
from PIL import Image, ImageDraw
P = 'packs/pikachu/textures/'
orig = lambda n: np.array(Image.open(glob.glob(f'template/textures/*/{n}.png')[0]).convert('RGBA'))

# FaceEventBlock00 (shown behind the gift after it opens): the gift box with its bow erased
g = np.array(Image.open(P + 'FaceEventHatenaBlock00.png').convert('RGBA')); n = g.copy()
yel = (g[..., 0] > 200) & (g[..., 1] > 150) & (g[..., 2] < 120) & (g[..., 3] > 128)
top = 111   # box top row of our gift art (measure yours)
n[:top] = 0
for y in range(top, 252):            # repaint the bow area row by row from a clean column on the right
    for x in range(96, 416):
        if x < 130 and g[y, x, 0] > 240 and g[y, x, 1] > 240: continue   # keep the white highlight
        n[y, x] = g[y, 430]
Image.fromarray(n).save(P + 'FaceEventBlock00.png')

# FaceEventMenuFrame00: the 9-slice menu frame without the ? block rivets
f = orig('FaceEventMenuFrame00'); f[9:55, 9:55] = f[32, 32]; Image.fromarray(f).save(P + 'FaceEventMenuFrame00.png')

# FaceEventMenuHatena00: white gift glyph (the game tints it grey)
S = 4; im = Image.new('RGBA', (128 * S, 128 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); T = (0, 0, 0, 0); cx = 64 * S
d.rounded_rectangle((12 * S, 40 * S, 116 * S, 124 * S), radius=12 * S, fill='white')
band = 82 * S; d.rectangle((12 * S, band - 5 * S, 116 * S, band + 5 * S), fill=T)
d.ellipse((cx - 17 * S, band - 17 * S, cx + 17 * S, band + 17 * S), fill=T); d.ellipse((cx - 10 * S, band - 10 * S, cx + 10 * S, band + 10 * S), fill='white')
d.ellipse((cx - 42 * S, 6 * S, cx - 4 * S, 38 * S), fill='white'); d.ellipse((cx + 4 * S, 6 * S, cx + 42 * S, 38 * S), fill='white')
d.ellipse((cx - 31 * S, 15 * S, cx - 13 * S, 29 * S), fill=T); d.ellipse((cx + 13 * S, 15 * S, cx + 31 * S, 29 * S), fill=T)
d.rectangle((12 * S, 34 * S, 116 * S, 40 * S), fill=T); d.rounded_rectangle((cx - 9 * S, 12 * S, cx + 9 * S, 34 * S), radius=5 * S, fill='white')
im.resize((128, 128), Image.LANCZOS).save(P + 'FaceEventMenuHatena00.png')
print('extras done')
