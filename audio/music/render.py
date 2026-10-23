"""Render looped Pokémon BGM stems -> packs/pikachu/audio/<clip>.wav + loops.json (sample loop points @32k)."""
import librosa, numpy as np, soundfile as sf, json, subprocess, os, sys
from scipy.signal import butter, sosfilt
SR=32000; OUT='../../packs/pikachu/audio'
loops=json.load(open(f'{OUT}/../music_loops.json')) if os.path.exists(f'{OUT}/../music_loops.json') else {}
def load(p): y,_=librosa.load(p,sr=SR,mono=False); return y if y.ndim==2 else np.vstack([y,y])
def refine(y,s,L):
    m=y.mean(0); seg=m[s:s+SR]; best=(-9,L)
    for d in range(-3000,3001):
        b=m[s+L+d:s+L+d+SR]; c=np.dot(seg,b)/(np.linalg.norm(seg)*np.linalg.norm(b)+1e-9)
        if c>best[0]: best=(c,L+d)
    return best[1],best[0]
def pick_start(y,L,lo,hi):
    m=librosa.feature.melspectrogram(y=y.mean(0),sr=SR,hop_length=320); m=librosa.power_to_db(m)
    best=(-9,0)
    for s in range(int(lo*100),int(hi*100),10):
        if s+L//320+300>m.shape[1]: break
        a=m[:,s:s+300]; b=m[:,s+L//320:s+L//320+300]
        c=-np.abs(a-b).mean()
        if c>best[0]: best=(c,s)
    return best[1]*320
def lufs(y,target):
    # simple RMS-based gain to target dBFS rms
    r=np.sqrt((y**2).mean()); g=10**(target/20)/r; return np.clip(y*g,-0.99,0.99)
# Stems are ADDITIVE layers (orig Luigi rms: Main -29, BigTouch -34, Touch -40, MiniTouch -49 dB);
# extra layers = band-filtered copies of the same track, so touching brightens/fattens it in phase.
LVL={'Main':0,'BigTouch':-5,'Touch':-11,'MiniTouch':-20}
def shelf(y,kind):
    if kind=='Main': return y
    if kind=='MiniTouch': sos=butter(2,5000,'high',fs=SR,output='sos')
    if kind=='Touch': sos=butter(2,2500,'high',fs=SR,output='sos')
    if kind=='BigTouch': sos=butter(2,[150,6000],'band',fs=SR,output='sos')
    return sosfilt(sos,y,axis=1)
def write(name,y,ls,le):
    sf.write(f'{OUT}/{name}.wav',y.T,SR,subtype='PCM_16'); loops[name]=[int(ls),int(le)] if le else None
    print(name,'%.1fs'%(y.shape[1]/SR),'loop',None if not le else (round(ls/SR,2),round(le/SR,2)))
def looped(src,L,lo,hi,prefix,stems,target=-29):
    y=load(src); L=int(L*SR); s=pick_start(y,L,lo,hi); L,c=refine(y,s,L)
    print(src,'start %.2f L %.3f corr %.3f'%(s/SR,L/SR,c))
    end=min(y.shape[1],s+L+SR); y=y[:,:end]
    y=lufs(y,target)
    for k in stems: write(prefix+k if k else prefix, lufs(shelf(y,K(k)),target+LVL[K(k)]), s, s+L)
K=lambda k:(k.split('.')[0].strip('_') if k and k.split('.')[0].strip('_') in LVL else 'Main')
ST=['Main','Touch','MiniTouch','BigTouch']
looped('src/center.wav',28.92,3,40,'Face_Luigi_',[x+'.yg' for x in ST])
looped('src/route1x.wav',45.80,19,30,'Face_Ground_',[x+'.sh' for x in ST])
looped('src/surf.wav',52.36,2,40,'Face_Underwater_',[x+'.sh' for x in ST])
looped('src/title.wav',43.37,5,45,'Face_MWTitle_',[x+'.sh' for x in ST])
looped('src/battle.wav',56.30,3,40,'Face_Star',['.sh','_Fever.sh'],-27)
# sleep: Poke Flute x3, gentle fade, one-shot
f=lufs(load('src/flute.wav'),-30); g=np.concatenate([f,np.zeros((2,SR*2)),f,np.zeros((2,SR*2)),f],1)
fade=np.ones(g.shape[1]); n=SR*4; fade[-n:]=np.linspace(1,0,n); write('Face_Sleep.sh',g*fade,0,0)
json.dump(loops,open(f'{OUT}/../music_loops.json','w'),indent=1)
