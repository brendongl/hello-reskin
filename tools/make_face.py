#!/usr/bin/env python3
"""Convert a flat face drawing (Pikachu v1) into the Luigi FaceSvgImageFile node layout.

Writes packs/<pack>/face_override/Luigi.pkl = {'svg': <typetree>, 'parts': <cPartsParamArray>}
and a preview PNG. Geometry is Luigi's skeleton with replaced/relocated parts.
"""
import copy, pickle, sys, os, json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage import measure
from shapely.geometry import Polygon, MultiPolygon, LineString, Point
from shapely.ops import unary_union
from shapely import affinity
import mapbox_earcut as earcut

sys.path.insert(0, os.path.dirname(__file__))
from svgtree import nodes

SRC = os.environ.get('FACE_SRC', 'packs/pikachu-reference/neutral_v1.png')   # flat front-facing face drawing on white
PACK = os.environ.get('PACK', 'packs/pikachu')
CX = CY = 1875.0                  # canvas centre (hinge origin, y-up)
HEAD_W = 520.0                    # target head width in canvas units
HEAD_C = (1875.0, 1990.0)         # target head centre (canvas, y-down)
STROKE = 14.0
SEG = 30.0                        # max perimeter segment length

def abgr(r, g, b, a=255): return (a << 24) | (b << 16) | (g << 8) | r
YELLOW = abgr(247, 211, 43); OUTLINE = abgr(74, 76, 83); BLACK = abgr(20, 20, 20)
RED = abgr(225, 72, 54); TONGUE = abgr(231, 36, 16)
SKIN = {0xffb7d5fa, 0xffb3d5f8}   # Luigi skin tones (ABGR)

# ---------- segmentation of the drawing ----------
im = np.array(Image.open(SRC).convert('RGB')).astype(int)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
white = (r > 225) & (g > 225) & (b > 225)
lab, _ = ndimage.label(white)
edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])); edge = edge[edge > 0]
sil = ndimage.binary_fill_holes(~np.isin(lab, edge))
sil = ndimage.binary_erosion(sil, iterations=3)          # outer stroke edge -> stroke centre

def mask_poly(m, simplify=0.8):
    cs = measure.find_contours(np.pad(m, 1).astype(float), 0.5)
    polys = [Polygon([(p[1] - 1, p[0] - 1) for p in c]).buffer(0) for c in cs if len(c) > 8]
    polys = [p for p in polys if p.area > 30]
    return unary_union(polys).simplify(simplify)

# cut ears from head along the junction lines
cut = Image.fromarray((sil * 255).astype('uint8')); d = ImageDraw.Draw(cut)
SPLIT_L = [(300, 434), (384, 368)]; SPLIT_R = [(640, 368), (730, 437)]
d.line(SPLIT_L, fill=0, width=3); d.line(SPLIT_R, fill=0, width=3)
cm = np.array(cut) > 0
lab, n = ndimage.label(cm)
comps = sorted([(ndimage.sum(cm, lab, i), i) for i in range(1, n + 1)], reverse=True)[:3]
head_m = lab == comps[0][1]
ears = [lab == c[1] for c in comps[1:]]
ears.sort(key=lambda m: np.argwhere(m)[:, 1].mean())     # left (viewer) first
head = mask_poly(ndimage.binary_dilation(head_m, iterations=2) & sil)
earL, earR = [mask_poly(ndimage.binary_dilation(e, iterations=2) & sil) for e in ears]

def comps_of(m, minsize):
    lab, n = ndimage.label(m); out = []
    for i in range(1, n + 1):
        mm = lab == i
        if mm.sum() >= minsize: out.append(mm)
    return out
blk = (r < 45) & (g < 45) & (b < 45)
tips = sorted([c for c in comps_of(blk, 2000)], key=lambda m: np.argwhere(m)[:, 1].mean())
nose_m = [c for c in comps_of(blk, 150) if c.sum() < 2000][0]
red = (r > 180) & (g < 110) & (b < 100)
cheeks = sorted(comps_of(red, 2000), key=lambda m: np.argwhere(m)[:, 1].mean())
grey = (r >= 45) & (r < 130) & (abs(r - g) < 25) & (abs(g - b) < 30)
gcomps = comps_of(grey, 500)
eyes = sorted([c for c in gcomps if 3000 < c.sum() < 12000], key=lambda m: np.argwhere(m)[:, 1].mean())
mouth_m = [c for c in gcomps if 800 < c.sum() < 3000][0]

tipL, tipR = [mask_poly(ndimage.binary_dilation(t, iterations=3)) for t in tips]
cheekL, cheekR = [mask_poly(ndimage.binary_dilation(c, iterations=2)) for c in cheeks]
nose = mask_poly(ndimage.binary_dilation(nose_m, iterations=1), 0.3)
mouth = mask_poly(mouth_m, 0.3)
eye_circ = []
for e in eyes:
    full = ndimage.binary_fill_holes(e); yx = np.argwhere(full)
    eye_circ.append((yx[:, 1].mean(), yx[:, 0].mean(), np.sqrt(full.sum() / np.pi)))

# ---------- image -> canvas transform ----------
hx0, hy0, hx1, hy1 = head.bounds
S = HEAD_W / (hx1 - hx0)
hcx, hcy = (hx0 + hx1) / 2, (hy0 + hy1) / 2
def T(geom): return affinity.affine_transform(geom, [S, 0, 0, S, HEAD_C[0] - hcx * S, HEAD_C[1] - hcy * S])
def Tp(x, y): return (HEAD_C[0] + (x - hcx) * S, HEAD_C[1] + (y - hcy) * S)
head, earL, earR, tipL, tipR, cheekL, cheekR, nose, mouth = map(T, (head, earL, earR, tipL, tipR, cheekL, cheekR, nose, mouth))
EYE_SCALE = float(os.environ.get('EYE_SCALE', '1.0'))
eye_c = [(*Tp(x, y), rr * S * EYE_SCALE) for x, y, rr in eye_circ]
def rel(x, y): return {'x': float(x - CX), 'y': float(CY - y)}   # canvas -> hinge coords

# ears extend under the head so a pulled ear never shows a gap
earL = unary_union([earL, head.intersection(earL.buffer(60))]).buffer(0)
earR = unary_union([earR, head.intersection(earR.buffer(60))]).buffer(0)
tipL, tipR = tipL.intersection(earL), tipR.intersection(earR)
cheekL, cheekR = cheekL.intersection(head.buffer(-STROKE / 2)), cheekR.intersection(head.buffer(-STROKE / 2))

# ---------- geometry helpers ----------
def densify(coords, seg=SEG):
    out = []
    for (x0, y0), (x1, y1) in zip(coords[:-1], coords[1:]):
        n = max(1, int(np.ceil(np.hypot(x1 - x0, y1 - y0) / seg)))
        for k in range(n): out.append((x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n))
    return out

def polys_of(geom):
    if geom.is_empty: return []
    if isinstance(geom, Polygon): return [geom]
    return [p for p in getattr(geom, 'geoms', []) if isinstance(p, Polygon) and p.area > 4]

def tess(poly, seg=SEG, tol=1.5):
    poly = poly.buffer(0).simplify(tol)
    if not poly.exterior.is_ccw: poly = Polygon(poly.exterior.coords[::-1], [h.coords for h in poly.interiors])
    rings = [densify(list(poly.exterior.coords), seg)] + [densify(list(h.coords), seg) for h in poly.interiors]
    verts = np.array([p for rg in rings for p in rg], dtype=np.float32)
    ends = np.cumsum([len(rg) for rg in rings]).astype(np.uint32)
    idx = earcut.triangulate_float32(verts, ends).tolist()
    perims, s = [], 0
    for rg in rings: perims.append({'Values': list(range(s, s + len(rg)))}); s += len(rg)
    x0, y0 = verts.min(0); x1, y1 = verts.max(0); w, h = max(x1 - x0, 1e-3), max(y1 - y0, 1e-3)
    return {'Vertices': [{'x': float(x), 'y': float(y)} for x, y in verts], 'Indices': idx, 'Perimeters': perims,
            'UVs': [{'x': float((x - x0) / w), 'y': float(1 - (y - y0) / h)} for x, y in verts],
            'UnclippedBounds': {'x': float(x0), 'y': float(y0), 'width': float(w), 'height': float(h)}}

def geoms(geom, seg=SEG, tol=1.5):
    ps = sorted(polys_of(geom), key=lambda p: -p.area)
    if len(ps) > 1: print('  note: dropped', len(ps) - 1, 'extra piece(s), areas', [round(p.area) for p in ps[1:]])
    return [tess(ps[0], seg, tol)] if ps else []   # Luigi nodes always hold exactly one geometry
def ring(poly, w=STROKE): return poly.buffer(w / 2).difference(poly.buffer(-w / 2))
def tiny(x, y, s=4): return Polygon([(x - s, y + s), (x + s, y + s), (x, y - s)])

def xform_geom(gm, fn):
    gm = copy.deepcopy(gm)
    for p in gm['Vertices']: p['x'], p['y'] = fn(p['x'], p['y'])
    xs = [p['x'] for p in gm['Vertices']]; ys = [p['y'] for p in gm['Vertices']]
    gm['UnclippedBounds'] = {'x': min(xs), 'y': min(ys), 'width': max(xs) - min(xs), 'height': max(ys) - min(ys)}
    return gm   # UVs kept: they index textures/gradients relative to the original shape

def node_bounds(N, n):
    xs, ys = [], []
    def walk(nd):
        for gm in nd['Geometries']:
            xs.extend(p['x'] for p in gm['Vertices']); ys.extend(p['y'] for p in gm['Vertices'])
        for c in nd['Children']: walk(N[int(c['rid'])])
    walk(n)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None

# ---------- rebuild the Luigi tree ----------
src = pickle.load(open('export/svgfiles.pkl', 'rb'))
key = [k for k in src if k[1] == 'Luigi_FaceGray00'][0]
svg = copy.deepcopy(src[key])
N = nodes(svg)
refs = {int(x['rid']): x for x in svg['references']['RefIds']}
next_rid = max(refs) + 1
byname = {}
for rid, n in N.items(): byname.setdefault(n['Name'], rid)
tops = [int(c['rid']) for c in N[int(N[svg['rootNode']['rid']]['Children'][0]['rid'])]['Children']]

def set_children(top, specs):
    """specs: list of (name, colour, [geometries]) -> replaces children of top node."""
    global next_rid
    old = [int(c['rid']) for c in N[top]['Children']]
    new = []
    for i, (name, col, gms) in enumerate(specs):
        if i < len(old):
            rid = old[i]
        else:
            rid = next_rid; next_rid += 1
            tmpl = copy.deepcopy(refs[old[0]]); tmpl['rid'] = str(rid) if isinstance(refs[old[0]]['rid'], str) else rid
            svg['references']['RefIds'].append(tmpl); refs[rid] = tmpl; N[rid] = tmpl['data']
        nd = N[rid]; nd['Name'] = name; nd['BaseColor'] = {'rgba': col}; nd['Geometries'] = gms
        nd['Children'] = []; nd['SettingIndexes'] = []
        new.append(rid)
    # drop surplus children
    N[top]['Children'] = [{'rid': rid} for rid in new]

head_top = (HEAD_C[0], head.bounds[1] + 70)
eyes_rel = {}

# eye layers: move/scale Luigi's textured eye geometry onto Pikachu's eyes
eye_hole = {}
lf = [x for x in N.values() if x['Name'] == 'Face00/0'][0]['Geometries'][0]
lholes = []
for per in lf['Perimeters'][1:]:
    pts = [(lf['Vertices'][i]['x'], lf['Vertices'][i]['y']) for i in per['Values']]
    if len(pts) >= 20: lholes.append(Polygon(pts).buffer(0))
lholes.sort(key=lambda p: p.centroid.x)                    # L (viewer-left) first
for side, (ex, ey, er), lh in zip('LR', eye_c, lholes):
    hb = lh.bounds
    sx, sy = 2 * er / (hb[2] - hb[0]), 2 * er / (hb[3] - hb[1])
    ocx, ocy = (hb[0] + hb[2]) / 2, (hb[1] + hb[3]) / 2
    fn = lambda x, y, sx=sx, sy=sy, ocx=ocx, ocy=ocy, ex=ex, ey=ey: (ex + (x - ocx) * sx, ey + (y - ocy) * sy)
    for layer in ('EyeLayer', 'EyelidLayer', 'CoverLayer'):
        for c in N[byname[f'Eye{side}_{layer}']]['Children']:
            nd = N[int(c['rid'])]; nd['Geometries'] = [xform_geom(gm, fn) for gm in nd['Geometries']]
            if os.environ.get('EYE_SMOOTH_LAYERS'):   # Luigi's layers are 25-point polygons -> visible facets; use a fine circle, same texture mapping
                gm = nd['Geometries'][0]; ub = gm['UnclippedBounds']
                ok = all(abs(uv['x'] - (v['x'] - ub['x']) / ub['width']) < 0.02 and abs(uv['y'] - (1 - (v['y'] - ub['y']) / ub['height'])) < 0.02 for v, uv in zip(gm['Vertices'], gm['UVs']))
                assert ok, 'eye layer UVs are not bounds-normalised'
                rc = min(er * 1.04, ub['width'] / 2 * 0.98, ub['height'] / 2 * 0.98)
                g2 = tess(Point(ex, ey).buffer(rc, 32), 6, 0.05)
                g2['UVs'] = [{'x': (v['x'] - ub['x']) / ub['width'], 'y': 1 - (v['y'] - ub['y']) / ub['height']} for v in g2['Vertices']]
                g2['UnclippedBounds'] = dict(ub); nd['Geometries'] = [g2]
    eye_hole[side] = affinity.affine_transform(lh, [sx, 0, 0, sy, ex - ocx * sx, ey - ocy * sy])
    if os.environ.get('EYE_CIRCLE'):        # perfectly round opening (Luigi's hole is egg-shaped)
        a = float(os.environ.get('EYE_ASPECT', '1.0'))   # width / height
        eye_hole[side] = affinity.scale(Point(ex, ey).buffer(er, 32), a ** 0.5, a ** -0.5)
    eyes_rel[side] = (ex, ey, er)
    # eyebrows (hidden) + kuma (hidden) sit near the eye
    for nm in [n for n in byname if n.startswith(f'Eyebrow{side}_')]:
        set_children(byname[nm], [(N[int(c['rid'])]['Name'], YELLOW, geoms(tiny(ex, ey - er - 20))) for c in N[byname[nm]]['Children']])
    set_children(byname[f'Kuma{side}00'], [(f'Kuma{side}00/0', YELLOW, geoms(tiny(ex, ey + er + 25)))])

head_fill = head.difference(eye_hole['L']).difference(eye_hole['R'])
head_line = ring(head)
set_children(byname['Face00'], [('Face00/0', YELLOW, geoms(head_fill, 12, 0.15)), ('Face00/1', OUTLINE, geoms(head_line)),
                                ('Face00/2', RED, geoms(cheekL)), ('Face00/3', RED, geoms(cheekR))])
# Face01 is the alternate head the game swaps to (sleep / twitch / pinch states) -> same head, outline, cheeks
set_children(byname['Face01'], [('Face01/0', YELLOW, geoms(head_fill, 12, 0.15)), ('Face01/1', YELLOW, geoms(head_fill, 12, 0.15)),
                                ('Face01/2', OUTLINE, geoms(head_line)), ('Face01/3', RED, geoms(cheekL)), ('Face01/4', RED, geoms(cheekR))])
set_children(byname['Face00Dummy'], [('Face00Dummy/0', abgr(229, 0, 18), geoms(head.buffer(-4), 120, 8))])

for side, ear, tip in (('L', earL, tipL), ('R', earR, tipR)):
    line = unary_union([ring(ear), tip.boundary.buffer(STROKE / 2).intersection(ear)])
    set_children(byname[f'Ear{side}_Normal00'], [(f'Ear{side}_Normal00/0', YELLOW, geoms(ear.buffer(2).buffer(-2), 30)),
                                                 (f'Ear{side}_Normal00/1', BLACK, geoms(tip)),
                                                 (f'Ear{side}_Normal00/2', OUTLINE, geoms(line))])

# nose
nb = nose.bounds; ncx, ncy = (nb[0] + nb[2]) / 2, (nb[1] + nb[3]) / 2
set_children(byname['NoseNormal00'], [('NoseNormal00/0', BLACK, geoms(nose.buffer(2), 12, 0.8)),
                                      ('NoseNormal00/1', OUTLINE, geoms(ring(nose.buffer(2), 4), 12, 0.8))])

# hidden Luigi-only parts -> tiny yellow specks inside the head
for nm in ('Hair01', 'Hair00', 'Cap_Front00', 'Cap_Back00', 'CapDummy'):
    set_children(byname[nm], [(N[int(c['rid'])]['Name'], YELLOW, geoms(tiny(*head_top))) for c in N[byname[nm]]['Children']])
if os.environ.get('EYE_BACKING', '1') == '1':
    # Cap_Back00 is drawn before the eye layers: give it a hole-free yellow head, so when a squish event deforms the
    # head's eye holes wider than the eyeballs, yellow shows through instead of the background
    kids = [N[int(c['rid'])]['Name'] for c in N[byname['Cap_Back00']]['Children']]
    set_children(byname['Cap_Back00'], [(kids[0], YELLOW, geoms(head.buffer(-STROKE / 2), 12, 0.15))] + [(k, YELLOW, geoms(tiny(*head_top))) for k in kids[1:]])
mb = mouth.bounds; mcx, mcy = (mb[0] + mb[2]) / 2, (mb[1] + mb[3]) / 2
for nm in [n for n in byname if n.startswith('Beard_')]:
    sx = -1 if ('L0' in nm or nm.endswith('L00') or 'NormalL' in nm or 'StrangeL' in nm) else 1
    cx = HEAD_C[0] + sx * 0.33 * HEAD_W
    if os.environ.get('BEARD_CHEEK', '0') == '1':   # tried 2026-10-23: the copy doesn't follow the face sway and peels off one side -> off   # moustache grab spots = the cheeks: idle it's hidden under the cheek, pulled it stretches a red cheek (no stray red speck)
        ck = cheekL if sx < 0 else cheekR
        set_children(byname[nm], [(N[int(c['rid'])]['Name'], RED, geoms(ck)) for c in N[byname[nm]]['Children']])
    else:
        set_children(byname[nm], [(N[int(c['rid'])]['Name'], YELLOW, geoms(tiny(cx, mcy, 2))) for c in N[byname[nm]]['Children']])   # yellow: no red speck, invisible when pulled

# mouths: Luigi mouth set moved under Pikachu's nose, skin recoloured; neutral mouths = Pikachu's cat mouth
lmb = node_bounds(N, N[byname['Mouth_Normal00']])
lmx, lmy = (lmb[0] + lmb[2]) / 2, (lmb[1] + lmb[3]) / 2
MS = 0.75
mfn = lambda x, y: (mcx + (x - lmx) * MS, mcy + (y - lmy) * MS)
for nm in [n for n in byname if n.startswith('Mouth_')] + ['Tongue_TongueLayer']:
    def walk(nd):
        nd['Geometries'] = [xform_geom(gm, mfn) for gm in nd['Geometries']]
        if nd['BaseColor']['rgba'] in SKIN: nd['BaseColor']['rgba'] = YELLOW
        for c in nd['Children']: walk(N[int(c['rid'])])
    walk(N[byname[nm]])
# Pikachu-style open mouths: no human teeth or skin-coloured lips inside; dark maroon inside, pink-red tongue.
# Outlines stay charcoal. A dark child is an outline when it's a thin ring (low fill ratio), else it's the mouth interior.
MOUTH_IN = abgr(112, 30, 36); PIKA_TONGUE = abgr(236, 92, 88)
WHITE = 0xffffffff
def fill_ratio(nd):
    a = 0.0; xs = []; ys = []
    for gm in nd['Geometries']:
        V = gm['Vertices']; I = gm['Indices']
        for i in range(0, len(I), 3):
            p, q, r = V[I[i]], V[I[i + 1]], V[I[i + 2]]
            a += abs((q['x'] - p['x']) * (r['y'] - p['y']) - (r['x'] - p['x']) * (q['y'] - p['y'])) / 2
        xs += [v['x'] for v in V]; ys += [v['y'] for v in V]
    return a / max(1e-6, (max(xs) - min(xs)) * (max(ys) - min(ys))) if xs else 1
if os.environ.get('PIKA_MOUTH', '1') == '1':
    for nm in [n for n in byname if n.startswith('Mouth_') and not n.startswith(('Mouth_Normal', 'Mouth_Grin', 'Mouth_Sad', 'Mouth_Wave'))]:
        has_outline = any(N[int(ch['rid'])]['Name'].startswith('Outline') for ch in N[byname[nm]]['Children'])
        def walkm(nd):
            c = nd['BaseColor']['rgba']; dark = (c & 0xff) < 90 and ((c >> 8) & 0xff) < 90
            if nd['Geometries'] and not nd['Name'].startswith('Outline'):
                if c in (WHITE, YELLOW): nd['BaseColor']['rgba'] = MOUTH_IN
                elif c in (0xff1024e7, 0xff0f29e7): nd['BaseColor']['rgba'] = PIKA_TONGUE
                elif dark and has_outline and fill_ratio(nd) > 0.55: nd['BaseColor']['rgba'] = MOUTH_IN
            for ch in nd['Children']: walkm(N[int(ch['rid'])])
        walkm(N[byname[nm]])
        # Luigi's lip band (between the outline and the mouth hole) shows the yellow face through -> grow the
        # first interior fill to the outline's inner edge (only if it is drawn before the tongue)
        kids = [N[int(ch['rid'])] for ch in N[byname[nm]]['Children']]
        if not has_outline:   # the dark base doubles as the outline: base -> maroon fill, the (ex-teeth) node -> charcoal ring on its rim
            base = [i for i, k in enumerate(kids) if k['Geometries'] and (k['BaseColor']['rgba'] & 0xff) < 90 and k['BaseColor']['rgba'] != MOUTH_IN and fill_ratio(k) > 0.55]
            teeth = [i for i, k in enumerate(kids) if k['Geometries'] and k['BaseColor']['rgba'] == MOUTH_IN and not k['Name'].startswith('Outline')]
            if base and teeth:
                bi = base[0]; bp = unary_union([Polygon([(gm['Vertices'][gm['Indices'][i + j]]['x'], gm['Vertices'][gm['Indices'][i + j]]['y']) for j in range(3)]).buffer(0.01)
                                                for gm in kids[bi]['Geometries'] for i in range(0, len(gm['Indices']), 3)])
                ins = bp.buffer(-STROKE * 0.42)
                if not ins.is_empty and ins.area > 0.25 * bp.area:
                    kids[bi]['BaseColor']['rgba'] = MOUTH_IN
                    kids[teeth[-1]]['BaseColor']['rgba'] = OUTLINE
                    kids[teeth[-1]]['Geometries'] = geoms(bp.buffer(0.5).difference(ins), 10, 0.5)
            continue
        def shp(nd):
            ts = []
            for gm in nd['Geometries']:
                V = gm['Vertices']; I = gm['Indices']
                ts += [Polygon([(V[I[i]]['x'], V[I[i]]['y']), (V[I[i + 1]]['x'], V[I[i + 1]]['y']), (V[I[i + 2]]['x'], V[I[i + 2]]['y'])]).buffer(0.01) for i in range(0, len(I), 3)]
            return unary_union(ts) if ts else None
        rings = sorted([k for k in kids if k['Geometries'] and (k['Name'].startswith('Outline') or (k['BaseColor']['rgba'] & 0xff) < 90 and k['BaseColor']['rgba'] != MOUTH_IN and fill_ratio(k) <= 0.55)], key=lambda k: not k['Name'].startswith('Outline'))
        inner = [i for i, k in enumerate(kids) if k['Geometries'] and k['BaseColor']['rgba'] == MOUTH_IN]
        tongue = [i for i, k in enumerate(kids) if k['BaseColor']['rgba'] == PIKA_TONGUE]
        if rings and inner and (not tongue or inner[0] < tongue[0]):
            holes = [Polygon(h) for r in polys_of(shp(rings[0])) for h in r.interiors]
            if not holes and shp(rings[0]) is not None:   # open (C-shaped) outline -> its hull
                holes = [shp(rings[0]).convex_hull.buffer(-STROKE * 0.3)]
            if holes:
                hole = max(holes, key=lambda h: h.area)
                have = unary_union([shp(kids[i]) for i in inner])
                if hole.area - have.intersection(hole).area > 0.08 * hole.area:
                    kids[inner[0]]['Geometries'] = geoms(hole.buffer(STROKE / 4), 10, 0.5)
set_children(byname['Mouth_Normal00'], [('Mouth_Normal00/0', YELLOW, geoms(mouth.buffer(3), 14, 0.8)), ('Mouth_Normal00/1', OUTLINE, geoms(mouth, 14, 0.8))])
set_children(byname['Mouth_Normal01'], [('Mouth_Normal01/0', OUTLINE, geoms(mouth, 14, 0.8))])

# glasses + snot bubble follow the new features
lE, rE = eyes_rel['L'], eyes_rel['R']
lel = node_bounds(src_N := nodes(src[key]), src_N[[r for r, n in src_N.items() if n['Name'] == 'EyeL_EyeLayer'][0]])
ler = node_bounds(src_N, src_N[[r for r, n in src_N.items() if n['Name'] == 'EyeR_EyeLayer'][0]])
gs = (rE[0] - lE[0]) / (((ler[0] + ler[2]) - (lel[0] + lel[2])) / 2)
gcx, gcy = ((lel[0] + lel[2]) / 2 + (ler[0] + ler[2]) / 2) / 2, ((lel[1] + lel[3]) / 2 + (ler[1] + ler[3]) / 2) / 2
ecx, ecy = (lE[0] + rE[0]) / 2, (lE[1] + rE[1]) / 2
gfn = lambda x, y: (ecx + (x - gcx) * gs, ecy + (y - gcy) * gs)
def walkx(nd, fn):
    nd['Geometries'] = [xform_geom(gm, fn) for gm in nd['Geometries']]
    for c in nd['Children']: walkx(N[int(c['rid'])], fn)
walkx(N[byname['Glass_Normal00']], gfn)
sb = node_bounds(src_N, src_N[[r for r, n in src_N.items() if n['Name'] == 'NoseNormal00'][0]])
dx, dy = ncx - (sb[0] + sb[2]) / 2, ncy - (sb[1] + sb[3]) / 2
walkx(N[byname['SnotBubble_Normal00']], lambda x, y: (x + dx, y + dy))

# ---------- touch / hinge parameters ----------
page = json.load(open('export/mb_FaceSvgPageLuigi.json'))
parts = copy.deepcopy(page['cPartsParamArray'])
for p in parts:
    path = p['cPath']
    if path.startswith('Ear'):
        side = path[3]
        base = LineString(SPLIT_L if side == 'L' else SPLIT_R).centroid
        bx, by = Tp(base.x, base.y)
        p['cHingedPos'] = rel(bx, by)
        cs = p['cCollisionSetting']; cs.update({'Left': 1.0, 'Right': 1.0, 'Top': 1.0, 'Bottom': 0.0, 'Offset': {'x': 0.0, 'y': 0.0}, 'Push': 40.0})
    elif path.startswith('NoseNormal'):
        p['cHingedPos'] = rel(ncx, ncy + 15)
    elif path.startswith('Mouth_i01'):
        p['cHingedPos'] = rel(mcx, mcy)
    elif path.startswith('Beard_'):
        p['cHingedPos'] = rel(HEAD_C[0], mcy + 20)

os.makedirs(f'{PACK}/face_override', exist_ok=True)
pickle.dump({'svg': svg, 'parts': parts}, open(f'{PACK}/face_override/Luigi.pkl', 'wb'))
json.dump({'scale': S, 'eyes': eye_c, 'nose': (ncx, ncy), 'mouth': (mcx, mcy),
           'ear_hinges': [p['cHingedPos'] for p in parts if p['cPath'].startswith('Ear')]}, open(f'{PACK}/face_override/Luigi_info.json', 'w'), indent=1)
print('ok scale', round(S, 3), 'nodes', len(svg['references']['RefIds']))
