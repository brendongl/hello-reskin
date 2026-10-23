#!/usr/bin/env python3
"""Copy the exported game textures (export/tex, from export_tex.py) into template/textures/<category>/<name>.png,
using template/MANIFEST.csv. These are YOUR copies from YOUR dump; they are never committed (see .gitignore)."""
import csv, json, os, shutil
ATLAS = {'b2746480': 'FaceAtlas_Luigi', '6cbf5da2': 'FaceAtlas_Mario', '3eb37a86': 'FaceAtlas_Peach', '92b616c5': 'FaceAtlas_Yoshi'}
rows = json.load(open('export/textures.json'))
by = {}
for r in rows:
    b = r['bundle'][:8]; name = r['name'] or ATLAS.get(b, '')
    by.setdefault((name, b), r['file'])
n = miss = 0
for m in csv.DictReader(open('template/MANIFEST.csv')):
    src = next((by[(m['texture'], b)] for b in m['bundles'].split() if (m['texture'], b) in by), None)
    if not src: miss += 1; print('missing', m['texture']); continue
    d = os.path.join('template', 'textures', m['category']); os.makedirs(d, exist_ok=True)
    shutil.copy(src, os.path.join(d, m['texture'] + '.png')); n += 1
print(n, 'templates written,', miss, 'missing')
