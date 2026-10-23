import UnityPy, os, sys, json, collections
root='romfs/Data'
files=[os.path.join(root,'StreamingAssets/aa/Switch',f) for f in sorted(os.listdir(root+'/StreamingAssets/aa/Switch'))]+[os.path.join(root,f) for f in ('sharedassets0.assets','resources.assets','globalgamemanagers.assets','level0')]
out=[]
for fp in files:
    env=UnityPy.load(fp)
    c=collections.Counter(); ex=collections.defaultdict(list)
    for o in env.objects:
        t=o.type.name; c[t]+=1
        if t in('Texture2D','Sprite','AudioClip','TextAsset','VideoClip','AnimationClip','Font','TMP_FontAsset'):
            try:
                d=o.read(); n=getattr(d,'m_Name','')
                info=n
                if t=='Texture2D': info=f"{n} {d.m_Width}x{d.m_Height} {d.m_TextureFormat.name if hasattr(d.m_TextureFormat,'name') else d.m_TextureFormat}"
                ex[t].append(info)
            except Exception as e: ex[t].append('ERR '+str(e)[:40])
    out.append({'file':os.path.basename(fp),'size':os.path.getsize(fp),'counts':dict(c),'examples':{k:v[:400] for k,v in ex.items()}})
    print(os.path.basename(fp), os.path.getsize(fp)//1024,'KB', {k:v for k,v in c.items() if k in('Texture2D','Sprite','AudioClip','AnimationClip','VideoClip','Mesh','Material','MonoBehaviour','TextAsset')}, flush=True)
json.dump(out,open('inventory.json','w'),indent=1)
