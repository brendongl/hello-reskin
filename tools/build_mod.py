#!/usr/bin/env python3
"""Build an Atmosphere LayeredFS mod for the Hello! (Mario/Luigi/Peach/Yoshi) Switch games.

Pack layout (packs/<name>/):
  pack.json                 {"name": "...", "title_id": "0100D8C0251AE000"}
  textures/<TexName>.png    replaces every Texture2D with that name (resized to original size)
  face/<Character>.json     {"colors": {"#00a63c": "#8000c0", ...}}  recolours FaceSvgImageFile parts
                            Character = Mario | Luigi | Peach | Yoshi

Output: build/<name>/atmosphere/contents/<TID>/romfs/Data/StreamingAssets/aa/Switch/<bundle>
Only bundles that changed are written.
"""
import struct, json, os, sys, glob, shutil, pickle, subprocess, ntpath
import numpy as np
from UnityPy.streams import EndianBinaryReader
from fsb5 import make_fsb_pcm16
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from env import AA, load

# unnamed face-part atlas per character bundle
ATLAS = {'b2746480': 'FaceAtlas_Luigi', '6cbf5da2': 'FaceAtlas_Mario', '3eb37a86': 'FaceAtlas_Peach', '92b616c5': 'FaceAtlas_Yoshi'}

def hex_to_abgr(h):
    h = h.lstrip('#'); r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    a = int(h[6:8], 16) if len(h) == 8 else 255
    return (a << 24) | (b << 16) | (g << 8) | r

def abgr_hex(v):
    return '#%02x%02x%02x' % (v & 255, (v >> 8) & 255, (v >> 16) & 255)

def main(pack_dir):
    pack = json.load(open(os.path.join(pack_dir, 'pack.json')))
    tid = pack.get('title_id', '0100D8C0251AE000').upper()
    out = os.path.join('build', pack['name'])
    dst = os.path.join(out, 'atmosphere', 'contents', tid, 'romfs', 'Data', 'StreamingAssets', 'aa', 'Switch')
    shutil.rmtree(out, ignore_errors=True); os.makedirs(dst)

    tex = {os.path.splitext(os.path.basename(p))[0]: p for p in glob.glob(os.path.join(pack_dir, 'textures', '*.png'))}
    faces = {os.path.splitext(os.path.basename(p))[0]: json.load(open(p)) for p in glob.glob(os.path.join(pack_dir, 'face', '*.json'))}
    overrides = {os.path.splitext(os.path.basename(p))[0]: pickle.load(open(p, 'rb')) for p in glob.glob(os.path.join(pack_dir, 'face_override', '*.pkl'))}
    shapes = {os.path.splitext(os.path.basename(p))[0]: json.load(open(p)) for p in glob.glob(os.path.join(pack_dir, 'shape', '*.json'))}  # <bundle prefix>.json: FaceSvgShape* field overrides
    lp = os.path.join(pack_dir, 'music_loops.json')
    loops = json.load(open(lp)) if os.path.exists(lp) else {}   # clip -> [loopstart, loopend] or null (stereo one-shot)
    tp = os.path.join(pack_dir, 'text.json')
    texts = json.load(open(tp)) if os.path.exists(tp) else {}   # exact message text -> replacement (MSBT 'Face' tables, every language)
    audio = {os.path.splitext(os.path.basename(p))[0]: p for p in glob.glob(os.path.join(pack_dir, 'audio', '*.wav'))}
    res_new = {}   # (bundle, resource name) -> bytearray
    used = set()

    env = load()
    dirty = set()
    for o in env.objects:
        bundle = o.assets_file.parent
        if o.type.name == 'Texture2D':
            d = o.read()
            key = d.m_Name or ATLAS.get(bundle.name[:8], '')
            if key in tex:
                img = Image.open(tex[key]).convert('RGBA')
                if img.size != (d.m_Width, d.m_Height):
                    img = img.resize((d.m_Width, d.m_Height), Image.LANCZOS)
                d.set_image(img)  # keeps original format (ASTC etc.) + Switch swizzle
                d.save(); dirty.add(bundle); used.add(key)
                print(f"tex  {key:32s} {d.m_Width}x{d.m_Height} -> {bundle.name[:8]}")
        elif o.type.name == 'AudioClip' and audio:
            a = o.read()
            if a.m_Name not in audio:
                continue
            rate = 32000
            ch = 2 if a.m_Name in loops else 1   # music: stereo + loop points from music_loops.json
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', audio[a.m_Name], '-ac', str(ch), '-ar', str(rate), '-f', 's16le', '-'], capture_output=True).stdout
            pcm = np.frombuffer(raw, np.int16)
            fsb = make_fsb_pcm16(pcm, rate, ch, loops.get(a.m_Name))
            rname = ntpath.basename(a.m_Resource.m_Source)
            key = (bundle, rname)
            if key not in res_new:
                res_new[key] = bytearray(bundle.files[rname].bytes)
            buf = res_new[key]
            buf += b'\0' * ((-len(buf)) % 32)
            a.m_Resource.m_Offset = len(buf); a.m_Resource.m_Size = len(fsb); buf += fsb
            a.m_CompressionFormat = 0; a.m_Frequency = rate; a.m_Channels = ch; a.m_BitsPerSample = 16
            a.m_Length = len(pcm) / ch / rate
            a.save(); dirty.add(bundle); used.add(a.m_Name)
        elif o.type.name == 'MonoBehaviour' and texts and o.read().m_Name == 'Face':
            # the table has managed references, which UnityPy can't re-serialise -> patch the aligned
            # length-prefixed strings (int32 len, utf-8, pad to 4) straight in the raw object data
            raw = bytes(o.get_raw_data()); n = 0
            enc = lambda t: (lambda b: struct.pack('<i', len(b)) + b + b'\0' * ((-len(b)) % 4))(t.encode('utf-8'))
            for a_, b_ in texts.items():
                c = raw.count(enc(a_)); raw = raw.replace(enc(a_), enc(b_)); n += c
            if n:
                o.set_raw_data(raw); dirty.add(bundle); used.add('text')
                print(f"text {bundle.name[:8]} {n} messages")
        elif o.type.name == 'MonoBehaviour' and (faces or overrides or shapes):
            try:
                tt = o.read_typetree()
            except Exception:
                continue
            if 'mUVOffsetMaxSpriteEye' in tt and bundle.name[:8] in shapes:
                for k, v in shapes[bundle.name[:8]].items(): tt[k] = v
                o.save_typetree(tt); dirty.add(bundle); used.add('shape:' + bundle.name[:8])
                print(f"shape {bundle.name[:8]} fields {list(shapes[bundle.name[:8]])}")
                continue
            if 'cPartsParamArray' in tt:
                char = next((c for c in overrides if 'Shape' + c in tt), None)
                if char:
                    tt['cPartsParamArray'] = overrides[char]['parts']
                    o.save_typetree(tt); dirty.add(bundle); used.add('parts:' + char)
                    print(f"parts {char} touch/hinge params replaced -> {bundle.name[:8]}")
                continue
            if 'rootNode' not in tt or 'sceneViewport' not in tt:
                continue
            char = tt['m_Name'].split('_')[0]
            if char in overrides:
                ov = overrides[char]['svg']
                tt['rootNode'] = ov['rootNode']; tt['references'] = ov['references']
                o.save_typetree(tt); dirty.add(bundle); used.add('face:' + char)
                print(f"face {tt['m_Name']:32s} geometry replaced ({len(ov['references']['RefIds'])} nodes) -> {bundle.name[:8]}")
                continue
            if char not in faces:
                continue
            remap = {hex_to_abgr(k): hex_to_abgr(v) for k, v in faces[char].get('colors', {}).items()}
            n = 0
            for ref in tt['references']['RefIds']:
                bc = ref['data'].get('BaseColor')
                if bc and (bc['rgba'] | 0xff000000) in {k | 0xff000000 for k in remap}:
                    for k, v in remap.items():
                        if (bc['rgba'] & 0xffffff) == (k & 0xffffff):
                            bc['rgba'] = (bc['rgba'] & 0xff000000) | (v & 0xffffff); n += 1; break
            o.save_typetree(tt); dirty.add(bundle); used.add('face:' + char)
            print(f"face {tt['m_Name']:32s} recoloured {n} parts -> {bundle.name[:8]}")

    for (b, rname), buf in res_new.items():
        old = b.files[rname]
        nr = EndianBinaryReader(bytes(buf)); nr.flags = old.flags
        b.files[rname] = nr
    if audio:
        print(f"audio {len(used & set(audio))}/{len(audio)} clips replaced")
    for name in set(tex) - used:
        print(f"WARN texture {name} not found in game")
    for b in dirty:
        path = os.path.join(dst, os.path.basename(b.name))
        with open(path, 'wb') as f:
            f.write(b.save(packer='lz4'))
        print('wrote', path, os.path.getsize(path))
    print('done ->', out)

if __name__ == '__main__':
    main(sys.argv[1])
