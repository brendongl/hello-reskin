#!/usr/bin/env python3
"""Render the coin spin frames as a Poké Ball turning about its vertical axis (flat sticker style, 3x supersampled)."""
import glob, numpy as np
from PIL import Image
RED, WHITE, DARK = np.array([230, 38, 46]), np.array([250, 250, 250]), np.array([79, 72, 70])
def ball(size, yaw_deg, S=3):
    N = size * S; R = N / 2 - 2 * S; line = 0.055
    yy, xx = np.mgrid[0:N, 0:N]; nx = (xx - N / 2 + .5) / R; ny = (yy - N / 2 + .5) / R
    rr = np.sqrt(nx ** 2 + ny ** 2); inside = rr <= 1
    nz = np.sqrt(np.clip(1 - nx ** 2 - ny ** 2, 0, 1)); t = np.radians(yaw_deg)
    ox = nx * np.cos(t) + nz * np.sin(t); oz = -nx * np.sin(t) + nz * np.cos(t)
    ang = np.arccos(np.clip(oz, -1, 1))                          # angle from the button axis
    col = np.where((ny < 0)[..., None], RED, WHITE).astype(float)
    band = np.abs(ny) < 0.075; col[band] = DARK
    col[ang < 0.36] = DARK; col[ang < 0.27] = WHITE
    ring = (ang > 0.15) & (ang < 0.19); col[ring] = DARK
    hl = ((nx + 0.42) / 0.16) ** 2 + ((ny + 0.55) / 0.09) ** 2 < 1; col[hl & (ny < -0.1)] = WHITE
    col[rr > 1 - line] = DARK
    a = inside.astype(float) * 255
    im = Image.fromarray(np.dstack([col, a]).astype('uint8'), 'RGBA')
    return im.resize((size, size), Image.LANCZOS)
yaws = {f'FaceEventCoin0{i}': 0 for i in range(5)}   # coin-style spin: front face squashed to each frame's outline (3D yaw + squash cut the button off)
for n, y in yaws.items():
    o = Image.open(glob.glob(f'template/textures/*/{n}.png')[0]).convert('RGBA')
    bb = o.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox(); h = bb[3] - bb[1]
    # the game's sprite mesh is trimmed to each coin frame's outline (thin when edge-on), so a full ball gets
    # clipped flat; squash the ball into that frame's outline at 94% so its edge stays round inside the mesh
    w = bb[2] - bb[0]; k = 0.94; bw, bh = max(8, int(w * k)), int(h * k)
    b = ball(h, y).resize((bw, bh), Image.LANCZOS); c = Image.new('RGBA', o.size, (0, 0, 0, 0))
    c.alpha_composite(b, (bb[0] + (w - bw) // 2, bb[1] + (h - bh) // 2))
    c.save(f'packs/pikachu/textures/{n}.png')
print('coins done')
