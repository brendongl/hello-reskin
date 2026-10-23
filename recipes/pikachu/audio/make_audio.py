#!/usr/bin/env python3
"""Map every Voice_Luigi_* clip to Pikachu clips (labelled by audio/label.py) and render replacement WAVs.

Output: packs/pikachu/audio/<LuigiClipName>.wav + packs/pikachu/audio_map.csv
Loudness is matched to the original Luigi clip; long lines are built by joining several clips.
"""
import tempfile, csv, glob, json, os, re, subprocess, sys, random
import numpy as np

RATE = 32000
OUT = 'packs/pikachu/audio'
random.seed(7)

# Luigi trigger -> preferred Pikachu categories (first has priority)
MAP = [
    (r'Grabbed', ['grab_short', 'pika_short', 'surprised']),
    (r'Pulled|PullMoustache|PullUpEyebrows|PullDownEyebrows|BeardMiddle', ['effort_grunt', 'surprised', 'scared', 'pika_short']),
    (r'ShakingHead', ['pika_short', 'curious_question']),
    (r'LargeSneeze|^.*_Sneeze$|Sneeze$', ['sneeze', 'surprised']),
    (r'CancelSneezing', ['curious_question', 'pika_short']),
    (r'AfterSneezing', ['giggle', 'happy']),
    (r'SnoringVoice', ['sleepy', 'tired_sigh']),
    (r'Snoring', ['__snore__']),
    (r'Yawn', ['yawn', 'sleepy']),
    (r'Smile|Wink|WavingHand|HatGreeting|FacePeek', ['happy', 'greeting_hello', 'giggle']),
    (r'Leaving', ['goodbye', 'sad', 'happy']),
    (r'Entering|PopOut', ['greeting_hello', 'excited_cheer', 'name_pikachu']),
    (r'ItsaMe|OhYeah|NumberOne', ['name_pikachu', 'excited_cheer']),
    (r'Flying|Rotate$|SpinJump|JumpInvincible|StarAround|JumpFinish|GoalPole|Flag|GetAllCoins|GetMushroom|ItemAppear|Pipe', ['excited_cheer', 'happy', 'chaa_attack']),
    (r'InkHit|Bwaaah|BooNotice', ['scared', 'surprised']),
    (r'InkRemoved', ['happy', 'giggle']),
    (r'MammaMia', ['sad', 'surprised']),
    (r'CheepCheepAppear', ['curious_question', 'surprised']),
    (r'CheepCheepHit', ['hurt', 'surprised', 'scared']),
    (r'CheepCheepSurprise|BooTakeHat|PeekabooSurprise', ['surprised']),
    (r'PeekabooBoo|PeekabooReveal', ['excited_cheer', 'happy']),
    (r'PeekabooHide|PeekabooSmirk|Tongue', ['giggle', 'happy']),
    (r'PeekabooGlimpse|PeekabooEyesHalfOpen', ['curious_question', 'giggle']),
    (r'PeekabooSmile', ['happy', 'giggle']),
    (r'PeekabooAngry', ['angry', 'sad']),
    (r'BlowingKiss', ['kiss_affection', 'happy']),
    (r'Singing', ['singing', 'happy']),
    (r'Dizzy', ['__join__', 'tired_sigh', 'sad', 'scared']),
    (r'Self', ['__join__', 'curious_question', 'happy', 'giggle', 'name_pikachu']),
]

def load_wav(path, rate=RATE):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(rate), '-f', 's16le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

def trim(x, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    return x[max(0, idx[0] - 160): idx[-1] + 320] if len(idx) else x

def rms(x): return float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0

# ---- Pikachu clip library ----
lib = {}
for lf in glob.glob('audio/clips/*/labels.json'):
    d = os.path.dirname(lf)
    for fn, v in json.load(open(lf)).items():
        if not (v.get('pikachu') and v.get('clean')): continue
        lib.setdefault(v['cat'], []).append(os.path.join(d, fn))
for k in lib: random.shuffle(lib[k])
use_count = {}
cache = {}
def clip(path):
    if path not in cache: cache[path] = trim(load_wav(path))
    return cache[path]

def pick(cats, target_len, used_here):
    best = None
    for c in cats:
        for p in lib.get(c, []):
            if p in used_here: continue
            L = len(clip(p)) / RATE
            score = abs(L - target_len) + 0.35 * use_count.get(p, 0) + 0.25 * cats.index(c)
            if best is None or score < best[0]: best = (score, p)
        if best and cats.index(c) == 0 and best[0] < 0.6: break
    return best[1] if best else None

def join(cats, target_len):
    parts, used, total = [], set(), 0.0
    while total < target_len * 0.85 and len(parts) < 6:
        p = pick(cats, min(1.2, target_len - total), used)
        if not p: break
        used.add(p); use_count[p] = use_count.get(p, 0) + 1
        x = clip(p); parts += [x, np.zeros(int(0.18 * RATE), np.float32)]; total += len(x) / RATE + 0.18
    return (np.concatenate(parts[:-1]) if parts else np.zeros(RATE // 2, np.float32)), used

def snore(target_len):
    base = [clip(p) for p in (lib.get('sleepy', []) + lib.get('yawn', []))[:4]] or [np.zeros(RATE // 2, np.float32)]
    out, i = [], 0
    while sum(len(o) for o in out) / RATE < target_len:
        b = base[i % len(base)] * 0.45
        out += [b, np.zeros(int(1.4 * RATE), np.float32)]; i += 1
    return np.concatenate(out)[: int(target_len * RATE)]

# ---- Luigi originals (for length + loudness) ----
sys.path.insert(0, 'tools')
import UnityPy
env = UnityPy.load('romfs/Data/StreamingAssets/aa/Switch/b274648008297a49c4b622eb69a22bb8.bundle')
luigi = {}
for o in env.objects:
    if o.type.name != 'AudioClip': continue
    a = o.read()
    if not a.m_Name.startswith('Voice_Luigi'): continue
    try:
        wav = list(a.samples.values())[0]
        tmp = os.path.join(tempfile.gettempdir(), f'luigi_{a.m_Name}.wav')
        open(tmp, 'wb').write(wav)
        x = load_wav(tmp)
    except Exception:
        x = np.zeros(int(a.m_Length * RATE), np.float32)
    luigi[a.m_Name] = (a.m_Length, rms(trim(x)), float(np.abs(x).max()) if len(x) else 0.5)

os.makedirs(OUT, exist_ok=True)
rows = []
for name in sorted(luigi):
    L, r0, pk0 = luigi[name]
    action = re.sub(r'^Voice_Luigi_(Face_)?(\d+[a-z]?_)?', '', name)
    cats = next((c for pat, c in MAP if re.search(pat, action)), ['happy', 'pika_short'])
    if cats[0] == '__snore__':
        y, src = snore(L), 'synth:sleepy-loop'
    elif cats[0] == '__join__' or L > 2.6:
        cc = [c for c in cats if not c.startswith('__')]
        y, used = join(cc, L); src = '+'.join(os.path.basename(p) for p in used)
    else:
        p = pick(cats, L, set())
        use_count[p] = use_count.get(p, 0) + 1
        y, src = clip(p), os.path.basename(p)
    # loudness match to Luigi's line, keep headroom
    if rms(y) > 0 and r0 > 0: y = y * (r0 / rms(y))
    if np.abs(y).max() > 0.95: y = y * (0.95 / np.abs(y).max())
    pcm = (y * 32767).astype(np.int16)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ar', str(RATE), '-ac', '1', '-i', '-', f'{OUT}/{name}.wav'], input=pcm.tobytes())
    rows.append([name, action, round(L, 2), round(len(y) / RATE, 2), cats[0], src])
with open('packs/pikachu/audio_map.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['luigi_clip', 'action', 'luigi_s', 'pikachu_s', 'category', 'source_clips']); w.writerows(rows)
print(len(rows), 'clips rendered ->', OUT)
