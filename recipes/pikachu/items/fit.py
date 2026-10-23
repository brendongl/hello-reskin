#!/usr/bin/env python3
"""Cut generated art off its white background and fit it into the original sprite's canvas/bbox.
Writes packs/pikachu/textures/<Name>.png"""
import glob, os, sys, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
OUT = 'packs/pikachu/textures'
def orig(name): return Image.open(glob.glob(f'template/textures/*/{name}.png')[0]).convert('RGBA')
def cutout(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)
    white = a.min(2) > 228
    lab, n = ndimage.label(white)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    bg = np.isin(lab, list(border))
    bg = ndimage.binary_dilation(bg, iterations=1) & (a.min(2) > 200) | bg   # eat the light AA fringe
    alpha = (~bg).astype(np.uint8) * 255
    alpha = np.asarray(Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.8)))
    im = Image.fromarray(np.dstack([a, alpha]).astype('uint8'), 'RGBA')
    return im.crop(im.getbbox())
def fit(art, name, rot=0, scale=1.0):
    o = orig(name); W, H = o.size
    ob = o.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox() or (0, 0, W, H)
    bw, bh = ob[2] - ob[0], ob[3] - ob[1]
    if rot: art = art.rotate(rot, resample=Image.BICUBIC, expand=True)
    k = min(bw / art.width, bh / art.height) * scale
    art = art.resize((max(1, round(art.width * k)), max(1, round(art.height * k))), Image.LANCZOS)
    x = ob[0] + (bw - art.width) // 2; y = ob[1] + (bh - art.height) // 2
    if ob[3] >= H - 2: y = H - art.height          # sprite cut off at the bottom (pops out of a pipe) -> keep it cut
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0)); canvas.alpha_composite(art, (max(0, x), max(0, y)) if x >= 0 and y >= 0 else (x, y)) if x >= 0 and y >= 0 else canvas.paste(art, (x, y), art)
    canvas.save(f'{OUT}/{name}.png'); return canvas
G = lambda n: cutout(f'work/items/gen/FaceEvent{n}.png')
direct = ['Mushroom00', 'Star00', 'HatenaBlock00', 'Kuribo00', 'Teresa00', 'Teresa01', 'Teresa02', 'Teresa03', 'Teresa04',
          'Pukupuku00', 'Pukupuku01', 'Pukupuku02', 'Gesso00', 'Bomb00', 'DokanNokonoko00', 'DokanNokonoko01',
          'DokanPakkun00', 'DokanPakkun01', 'Apple00', 'Cap01', 'NoteBlock00', 'Toad00', 'Toad02', 'ToadHand00']
for n in direct: fit(G(n), 'FaceEvent' + n)
for b, src in [('Mushroom00', 'Mushroom00'), ('Star00', 'Star00'), ('HatenaBlock00', 'HatenaBlock00'), ('Pukupuku00', 'Pukupuku00'), ('Gesso00', 'Gesso00')]:
    fit(G(src), 'FaceBtn' + b)
for i, r in enumerate([-6, -2, 2, 6]): fit(G('Gesso00'), f'FaceEventGessoMini0{i}', rot=r)   # wiggle frames
print('fitted', len(direct) + 5 + 4)
