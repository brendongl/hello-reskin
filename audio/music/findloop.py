import librosa, numpy as np, sys
SR=32000
def find(path, lo, hi, s_min=1.0):
    y,_=librosa.load(path,sr=SR,mono=True)
    hop=320  # 100 fps
    C=librosa.feature.chroma_cqt(y=y,sr=SR,hop_length=hop); M=librosa.power_to_db(librosa.feature.melspectrogram(y=y,sr=SR,hop_length=hop,n_mels=64))
    F=np.vstack([C*3,(M-M.mean())/M.std()]); F=F/ (np.linalg.norm(F,axis=0)+1e-9)
    n=F.shape[1]; best=(-1,0)
    for L in range(int(lo*100),min(int(hi*100),n-300)):
        w=min(n-L,int(20*100))
        a=int(s_min*100); 
        if a+w+L>n: w=n-L-a
        if w<300: continue
        sc=(F[:,a:a+w]*F[:,a+L:a+L+w]).sum(0).mean()
        if sc>best[0]: best=(sc,L)
    return y,best
if __name__=='__main__':
    y,(sc,L)=find(sys.argv[1],float(sys.argv[2]),float(sys.argv[3]))
    print(sys.argv[1],'dur %.1f'%(len(y)/SR),'loop %.2fs score %.3f'%(L/100,sc))
