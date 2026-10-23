#!/usr/bin/env python3
"""StarList00 (4x3 spin sheet of the flying Super Star) -> spinning Thunder Stone: each cell gets the art squashed to that frame's width."""
import sys, numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, 'items'); from fit import cutout
o = Image.open('template/textures/ui/StarList00.png').convert('RGBA'); A = np.asarray(o)[..., 3] > 30
art = cutout('work/items/gen/FaceEventStar00.png'); back = art.transpose(Image.FLIP_LEFT_RIGHT)
lab, n = ndimage.label(ndimage.binary_dilation(A, iterations=3))
out = Image.new('RGBA', o.size, (0, 0, 0, 0)); k = 0
objs = sorted(ndimage.find_objects(lab), key=lambda s: (s[0].start // 200, s[1].start))
for sl in objs:
    h = sl[0].stop - sl[0].start; w = sl[1].stop - sl[1].start
    if h < 40: continue
    src = art if k % 12 < 6 else back                      # second half of the spin shows the back
    im = src.resize((max(2, w), h), Image.LANCZOS)
    out.alpha_composite(im, (sl[1].start, sl[0].start)); k += 1
out.save('packs/pikachu/textures/StarList00.png'); print('frames', k)
