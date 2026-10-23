#!/usr/bin/env python3
"""Generate/edit images via OpenRouter (Gemini image models).

usage: gen_image.py -o out.png [-m MODEL] [-i ref.png ...] "prompt"
Writes out.png (and out_2.png ... if several images come back) + out.json (raw response text).
"""
import argparse, base64, json, mimetypes, os, sys, urllib.request

def key():
    k = os.environ.get('OPENROUTER_API_KEY')
    if not k: sys.exit('set OPENROUTER_API_KEY (https://openrouter.ai/keys)')
    return k

def data_url(p):
    mt = mimetypes.guess_type(p)[0] or 'image/png'
    return f"data:{mt};base64," + base64.b64encode(open(p, 'rb').read()).decode()

ap = argparse.ArgumentParser()
ap.add_argument('prompt'); ap.add_argument('-o', '--out', required=True)
ap.add_argument('-m', '--model', default='google/gemini-3-pro-image')
ap.add_argument('-i', '--image', action='append', default=[])
ap.add_argument('--aspect', help='e.g. 1:1, 16:9')
a = ap.parse_args()

content = [{'type': 'text', 'text': a.prompt}] + [{'type': 'image_url', 'image_url': {'url': data_url(p)}} for p in a.image]
body = {'model': a.model, 'modalities': ['image', 'text'], 'messages': [{'role': 'user', 'content': content}]}
if a.aspect:
    body['image_config'] = {'aspect_ratio': a.aspect}
req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', json.dumps(body).encode(),
                             {'Authorization': 'Bearer ' + key(), 'Content-Type': 'application/json'})
try:
    r = json.load(urllib.request.urlopen(req, timeout=300))
except urllib.error.HTTPError as e:
    sys.exit(f"HTTP {e.code}: {e.read().decode()[:500]}")
msg = r['choices'][0]['message']
imgs = msg.get('images') or []
base, ext = os.path.splitext(a.out)
for n, im in enumerate(imgs):
    url = im['image_url']['url']
    path = a.out if n == 0 else f"{base}_{n + 1}{ext}"
    open(path, 'wb').write(base64.b64decode(url.split(',', 1)[1]))
    print('wrote', path)
json.dump({'model': a.model, 'text': msg.get('content'), 'usage': r.get('usage'),
           'finish': r['choices'][0].get('finish_reason')}, open(base + '.json', 'w'), indent=1)
if not imgs:
    sys.exit(f"no image returned: finish={r['choices'][0].get('finish_reason')} text={str(msg.get('content'))[:300]}")
