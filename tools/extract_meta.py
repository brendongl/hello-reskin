#!/usr/bin/env python3
"""Dump the face vector files and face parameter MonoBehaviours the face tools need:
export/svgfiles.pkl (FaceSvgImageFile meshes) and export/mb_<name>.json (page/shape/touch params).
Needs dump/DummyDll from Il2CppDumper (see docs/GUIDE.md)."""
import sys, json, pickle, os
sys.path.insert(0, os.path.dirname(__file__)); from env import load
os.makedirs('export', exist_ok=True)
env = load(); svg = {}; n = 0
WANT = ('FaceSvgPage', 'FaceSvgShape', 'FaceAutoPartsTouchParams', 'PageParamChar', 'FaceSvgCharacterParam')
for o in env.objects:
    if o.type.name != 'MonoBehaviour': continue
    try:
        d = o.read_typetree(); cls = o.read().m_Script.read().m_ClassName
    except Exception: continue
    if cls == 'FaceSvgImageFile':
        svg[(o.assets_file.parent.name if o.assets_file.parent else o.assets_file.name, d['m_Name'], o.path_id)] = d
    elif cls.startswith(WANT):
        name = d.get('m_Name') or cls
        json.dump(d, open(f'export/mb_{name}.json', 'w'), default=str, indent=1); n += 1
pickle.dump(svg, open('export/svgfiles.pkl', 'wb'))
print(len(svg), 'svg files,', n, 'param files')
