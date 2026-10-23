import json, os, sys
from PIL import Image
import numpy as np
from scipy import ndimage
src=Image.open('template/textures/face_atlas/FaceAtlas_Luigi.png').convert('RGBA')
a=np.array(src).astype(float); rgb=a[...,:3]
P=json.load(open(sys.argv[1])) if len(sys.argv)>1 else {}
YEL=np.array([247,211,43.]); DARK=np.array(P.get('eye_rgb',[32,32,36]),float); IRIS=DARK; WHITE=np.array([252,252,252.])
skin=np.array([250,213,183.])
ds=np.linalg.norm(rgb-skin,axis=2)
bg=np.all(np.abs(rgb-205)<4,axis=2)                       # unused atlas background
skin_core=ndimage.binary_dilation(ds<25,iterations=3)
t=(np.clip(1-ds/60,0,1)*skin_core)[...,None]; out=rgb*(1-t)+YEL*t
blue=(rgb[...,2]-rgb[...,0]>40)&(rgb[...,2]>120); out[blue]=IRIS
lum=rgb.min(axis=2)
white=(lum>200)&~bg
darkln=(rgb.max(axis=2)<130)&~blue
red=(rgb[...,0]>200)&(rgb[...,1]<90)
near_red=ndimage.binary_dilation(red,iterations=40)
# highlights: small white blobs enclosed by pupil colours
lab,n=ndimage.label(white); keep=np.zeros_like(white)
for i,s in enumerate(ndimage.sum(white,lab,range(1,n+1)),1):
    if s<4000:
        m=lab==i; rg=ndimage.binary_dilation(m,iterations=3)&~m
        if (darkln[rg]|blue[rg]).mean()>0.6: keep|=m
keep|=white&near_red
# white (and its anti-aliased edge toward lines) -> dark
soft=(lum>130)&~skin_core&~blue&~bg&~keep&~(red|near_red&(lum<=200))
out[soft]=DARK
# glyphs on white (X, spiral): dark strokes without holes, far from skin
gl,gn=ndimage.label(darkln); skin_near=ndimage.binary_dilation(ds<25,iterations=6); ng=0
for i in range(1,gn+1):
    m=gl==i
    if m.sum()<300 or (m&skin_near).any(): continue
    if ndimage.binary_fill_holes(m).sum()>m.sum()*1.3: continue
    rg=ndimage.binary_dilation(m,iterations=4)&~m
    if white[rg].mean()>0.5: out[ndimage.binary_dilation(m,iterations=1)]=WHITE; ng+=1
print('glyphs',ng)
# grey iris outline / inner pupil (grey strokes touching the iris) -> same dark, so the eye reads as one disc
bl=ndimage.binary_dilation(blue,iterations=3); ni=0
for i in range(1,gn+1):
    m=gl==i
    if (m&bl).any() and not (m&skin_near).any(): out[m]=DARK; ni+=1
print('iris strokes',ni)
# Pikachu highlight: big white disc up-left of each iris (replaces Luigi's small dot).
# Atlas content is squashed into a circle on screen by Luigi's hole aspect (148x211), so draw a tall ellipse.
ASPECT = 211.0 / 148.0
irises = ndimage.binary_fill_holes(blue)
il, inn = ndimage.label(irises); nh = 0
from PIL import ImageDraw
img = Image.fromarray(np.dstack([out, a[..., 3:]]).clip(0, 255).astype('uint8'))
dr = ImageDraw.Draw(img)
DIAG = [(255,0,0),(0,255,0),(0,0,255),(255,255,0),(255,0,255),(0,255,255),(255,128,0),(128,0,255)]
side_of = P.get('side_of', {})            # iris index -> 'L' or 'R' (viewer side)
k2 = 0
for k, sl in enumerate(ndimage.find_objects(il), 1):
    m = il[sl] == k
    if m.sum() < 1500: continue
    y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
    w, h = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    region = np.zeros(white.shape, bool); region[sl] = m
    grow = ndimage.binary_dilation(region, iterations=4)
    if P.get('clean_iris'):   # wipe leftover outline specks around the old iris (they alias into noise when minified)
        grow = ndimage.binary_dilation(region, iterations=P['clean_iris'])
        o = np.array(img); o[grow & (o[..., 3] > 0)] = list(DARK.astype(int)) + [255]; img = Image.fromarray(o); dr = ImageDraw.Draw(img)
    else:
        o = np.array(img); o[grow & keep & white] = list(DARK.astype(int)) + [255]; img = Image.fromarray(o); dr = ImageDraw.Draw(img)
    k2 += 1
    if P.get('no_iris_hl'): continue   # highlight lives on the open-eyelid cell instead (static under glances)
    if P.get('diag'):
        rx = 0.25 * w; ry = rx * ASPECT; hx, hy = cx, cy; col = DIAG[k2 - 1]
    else:
        sgn = 1 if side_of.get(str(k2), 'L') == 'L' else -1      # +x = toward the nose for the viewer-left eye
        rx = P.get('hl_rx', 0.36) * w; ry = rx * P.get('hl_aspect', ASPECT)
        hx = cx + sgn * P.get('hl_dx', -0.22) * w + P.get('off_' + side_of.get(str(k2), 'L'), [0, 0])[0] * w
        hy = cy + P.get('hl_dy', -0.30) * h + P.get('off_' + side_of.get(str(k2), 'L'), [0, 0])[1] * h
        col = tuple(P.get('hl_rgb', [252, 252, 252]))
    soft = P.get('hl_soft', 0)
    if soft:   # anti-aliased edge `soft` atlas px wide: the game minifies the atlas ~4x, so a hard edge aliases into a lumpy blob
        o = np.array(img).astype(float); pad = max(rx, ry) * 1.3 + soft * 2; x0e, x1e = int(hx - pad), int(hx + pad) + 1; y0e, y1e = int(hy - pad), int(hy + pad) + 1
        yy, xx = np.mgrid[y0e:y1e, x0e:x1e]
        E2 = P.get('hl_E2_' + side_of.get(str(k2), 'L')) if not P.get('diag') else None
        if E2 is not None:   # pre-distorted ellipse (vT E2^-1 v < 1) that the game's eye warp turns into a circle
            Mi = np.linalg.inv(np.array(E2)); vx, vy = xx - hx, yy - hy
            dn = np.sqrt(Mi[0, 0] * vx * vx + 2 * Mi[0, 1] * vx * vy + Mi[1, 1] * vy * vy)
            rx = ry = float(np.sqrt(np.linalg.eigvalsh(np.array(E2)).min()))
        else:
            dn = np.sqrt(((xx - hx) / rx) ** 2 + ((yy - hy) / ry) ** 2)
        al = np.clip((1 - dn) * min(rx, ry) / soft + 0.5, 0, 1)[..., None]
        o[y0e:y1e, x0e:x1e, :3] = o[y0e:y1e, x0e:x1e, :3] * (1 - al) + np.array(col[:3]) * al
        img = Image.fromarray(o.clip(0, 255).astype('uint8')); dr = ImageDraw.Draw(img)
    else:
        dr.ellipse([hx - rx, hy - ry, hx + rx, hy + ry], fill=col + (255,))
    nh += 1

# eyelid ring: the dark outline around each transparent eyelid hole shows as a rim around the eye on screen
if 'lid_ring_rgb' in P:
    o = np.array(img); al = o[..., 3] < 128
    tl, tn = ndimage.label(al); nr = 0
    for k, sl in enumerate(ndimage.find_objects(tl), 1):
        mm = tl[sl] == k; hh, ww = mm.shape
        if not (15000 < mm.sum() < 120000) or not (0.4 < ww / hh < 0.9) or mm.sum() / (ww * hh) < 0.6: continue
        reg = np.zeros(al.shape, bool); reg[sl] = mm
        ring = ndimage.binary_dilation(reg, iterations=P.get('lid_ring_px', 16)) & ~reg & darkln
        if P.get('lid_fill_px'):            # also paint the skin around the hole, so the visible opening is set by the head hole
            sl2 = tuple(slice(max(0, q.start - 120), q.stop + 120) for q in sl)    # round (Euclidean) growth, not the diamond of binary_dilation
            dist = ndimage.distance_transform_edt(~reg[sl2]); grow = np.zeros_like(reg); grow[sl2] = dist <= P['lid_fill_px']
            ring |= grow & ~reg & (o[..., 3] > 0)
        if P.get('lid_open_clear') and [sl[1].start, sl[0].start] in P.get('lid_open_cells', []):   # plain open-eye lid: clear its rim so the eye texture (and highlight) is never clipped
            sl2 = tuple(slice(max(0, q.start - 120), q.stop + 120) for q in sl)
            dist = ndimage.distance_transform_edt(~reg[sl2]); grow = np.zeros_like(reg); grow[sl2] = dist <= P['lid_open_clear']
            dark = np.zeros_like(reg); dark[sl2] = dist <= P.get('lid_fill_px', 60)
            o[dark & ~grow & (o[..., 3] > 0), :3] = P['lid_ring_rgb']        # keep a dark rim beyond the opening: covers the eyeball when gaze shifts it
            o[grow & ~reg & (o[..., 3] > 0), 3] = 0; nr += 1; print('  opened lid', sl[1].start, sl[0].start)
            HL = P.get('hl_lid')   # static highlight painted on the open-eyelid cell (the eye texture is UV-shifted by glances; the lid is not)
            if HL or P.get('lid_diag'):
                ci = P['lid_open_cells'].index([sl[1].start, sl[0].start]); y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
                w_, h_ = x1 - x0, y1 - y0; cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
                if P.get('lid_diag'):
                    hc = HLd = dict(rx=0.18, aspect=1.0, dx=0.25, dy=-0.25); colr = [(255, 0, 0), (0, 0, 255)][ci]
                else:
                    hc = dict(HL); hc.update(HL.get('cell%d' % ci, {})); colr = tuple(P.get('hl_rgb', [252, 252, 252]))
                rx_ = hc['rx'] * w_; ry_ = rx_ * hc.get('aspect', 1.0); hx_ = cx_ + hc['dx'] * w_; hy_ = cy_ + hc['dy'] * h_
                pad = max(rx_, ry_) * 1.3 + 20; xa, xb, ya, yb = int(hx_ - pad), int(hx_ + pad) + 1, int(hy_ - pad), int(hy_ + pad) + 1
                yy, xx = np.mgrid[ya:yb, xa:xb]; dn = np.sqrt(((xx - hx_) / rx_) ** 2 + ((yy - hy_) / ry_) ** 2)
                sf = P.get('hl_soft', 9); al_ = np.clip((1 - dn) * min(rx_, ry_) / sf + 0.5, 0, 1)
                sub = o[ya:yb, xa:xb].astype(float)
                a0 = sub[..., 3:4] / 255; a1 = al_[..., None] + a0 * (1 - al_[..., None])        # 'over' onto possibly transparent lid pixels
                sub[..., :3] = np.where(a1 > 0, (np.array(colr) * al_[..., None] + sub[..., :3] * a0 * (1 - al_[..., None])) / np.maximum(a1, 1e-6), sub[..., :3])
                sub[..., 3:4] = a1 * 255; o[ya:yb, xa:xb] = sub.clip(0, 255).astype('uint8')
                print('  lid highlight cell', ci, 'at', round(hx_), round(hy_), 'r', round(rx_))
            continue
        o[ring, :3] = P['lid_ring_rgb']; nr += 1
    img = Image.fromarray(o); print('lid rings', nr)
if P.get('seam_fix'):   # thin white seams left between ex-sclera (now dark) cells and skin cells: event glances UV-shift the eye into them
    o = np.array(img); ww = (o[..., :3].min(2) > 225) & (o[..., 3] > 200)
    sl_, sn = ndimage.label(ww); ns = 0
    dk = np.all(np.abs(o[..., :3].astype(int) - DARK.astype(int)) < 12, axis=2)
    for i, sl in enumerate(ndimage.find_objects(sl_), 1):
        hh, wd = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        m = sl_[sl] == i
        if min(hh, wd) > 8 and m.sum() > 0.25 * hh * wd: continue          # solid blob (highlight/glyph), not a seam line
        big = tuple(slice(max(0, q.start - 4), q.stop + 4) for q in sl)
        mm = np.zeros(ww.shape, bool); mm[sl] = m
        rg = ndimage.binary_dilation(mm[big], iterations=3) & ~mm[big]
        if dk[big][rg].mean() > 0.15:
            o[mm, :3] = DARK.astype(int); ns += 1
    img = Image.fromarray(o); print('seams fixed', ns)
if P.get('tongue_cell'):   # stick-out tongue cell: no human teeth, Pikachu pink-red tongue (matches the vector mouths)
    o = np.array(img); x0, y0, x1, y1 = P['tongue_cell']; c = o[y0:y1, x0:x1]
    wt = (c[..., :3].min(2) > 235) & (c[..., 3] > 200); c[wt, :3] = [112, 30, 36]
    rd = (c[..., 0] > 180) & (c[..., 1] < 90) & (c[..., 2] < 80); c[rd, :3] = [236, 92, 88]
    img = Image.fromarray(o); print('tongue cell recoloured', int(wt.sum()), int(rd.sum()))
out = np.array(img)[..., :3].astype(float); a[..., 3] = np.array(img)[..., 3]
print('highlights', nh)
res=np.dstack([out,a[...,3:]]).clip(0,255).astype('uint8')
Image.fromarray(res).save(P.get('out', os.environ.get('PACK', 'packs/pikachu') + '/textures/FaceAtlas_Luigi.png'))
c=Image.fromarray(res).crop((0,1500,2048,4096)); c.thumbnail((700,900)); c.save('export/atlas_pika_preview.png')
