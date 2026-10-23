import pickle,sys,re
from PIL import Image, ImageDraw
sys.path.insert(0,'tools'); from svgtree import nodes
def col(rgba): return (rgba&255,(rgba>>8)&255,(rgba>>16)&255,(rgba>>24)&255)
def render(v,out,skip=None,scale=0.25):
    N=nodes(v); W,H=v['size']['x'],v['size']['y']
    im=Image.new('RGBA',(int(W*scale),int(H*scale)),(200,200,200,255)); dr=ImageDraw.Draw(im)
    order=[]
    def walk(rid,top):
        n=N[rid]; t=top or n['Name']
        for g in n.get('Geometries') or []: order.append((t,n,g))
        for c in n.get('Children') or []: walk(int(c['rid']), top if top else (n['Name'] if n['Name'] not in('','_1') else None))
    walk(v['rootNode']['rid'],None)
    for t,n,g in order:
        if skip and skip(t): continue
        vs=[(p['x']*scale,p["y"]*scale) if True else None for p in g['Vertices']]; ix=g['Indices']
        c=col(n['BaseColor']['rgba'])
        if n.get('SettingIndexes'): c=(255,0,255,120)
        for i in range(0,len(ix),3): dr.polygon([vs[ix[i]],vs[ix[i+1]],vs[ix[i+2]]],fill=c)
    im.save(out); return [t for t,_,_ in order]
if __name__=='__main__':
    d=pickle.load(open('export/svgfiles.pkl','rb'))
    for k,v in d.items():
        keep=re.compile(r'^(Mouth_Normal00|Mouth_)') 
        tops=render(v,f"export/face_{k[1]}.png",skip=lambda t:(t.startswith('Mouth_') and t!='Mouth_Normal00') or 'Dummy' in t or t.startswith('Kuma') or 'Cover' in t or 'Eyelid' in t)
