import UnityPy, os, json
root='romfs/Data'; outd='export/tex'; os.makedirs(outd,exist_ok=True)
files=[os.path.join(root,'StreamingAssets/aa/Switch',f) for f in sorted(os.listdir(root+'/StreamingAssets/aa/Switch'))]+[os.path.join(root,f) for f in ('sharedassets0.assets','resources.assets','globalgamemanagers.assets')]
rows=[]
for fp in files:
    env=UnityPy.load(fp); b=os.path.basename(fp)[:8]
    for o in env.objects:
        if o.type.name!='Texture2D': continue
        d=o.read()
        try:
            img=d.image; fn=f"{outd}/{b}_{d.m_Name}_{o.path_id}.png"[:200]; img.save(fn)
            rows.append(dict(bundle=os.path.basename(fp),name=d.m_Name,pid=o.path_id,w=d.m_Width,h=d.m_Height,fmt=str(d.m_TextureFormat),file=fn))
        except Exception as e: print('fail',b,d.m_Name,e)
json.dump(rows,open('export/textures.json','w'),indent=1); print(len(rows))
