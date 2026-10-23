import sys, os, subprocess, numpy as np, json
src, outdir, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
raw = subprocess.run(['ffmpeg','-v','error','-i',src,'-ac','1','-ar','48000','-f','s16le','-'],capture_output=True).stdout
x = np.frombuffer(raw, np.int16).astype(np.float32)/32768
win = 480; n = len(x)//win
rms = np.sqrt((x[:n*win].reshape(n,win)**2).mean(1))
thr = max(0.012, np.percentile(rms, 30)*3)
on = rms > thr
# merge gaps < 0.25s, drop clips < 0.12s
segs=[]; i=0
while i<n:
    if on[i]:
        j=i
        while j<n and (on[j] or (on[j:j+25].any())): j+=1
        segs.append((i,j)); i=j
    else: i+=1
segs=[(a,b) for a,b in segs if (b-a)*win/48000>0.12]
meta=[]
for k,(a,b) in enumerate(segs):
    s=max(0,(a-3)*win); e=min(len(x),(b+5)*win)
    clip=x[s:e]
    fn=f"{outdir}/{prefix}_{k:03d}.wav"
    subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar','48000','-ac','1','-i','-',fn],input=clip.tobytes())
    meta.append(dict(file=os.path.basename(fn),start=round(s/48000,2),dur=round(len(clip)/48000,2),peak=round(float(np.abs(clip).max()),2)))
json.dump(meta,open(f"{outdir}/{prefix}_index.json",'w'),indent=1)
print(len(meta),'clips', 'thr',round(thr,4))
