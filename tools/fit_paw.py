import sys
from PIL import Image
import numpy as np
from scipy import ndimage
def cut(p):
    f=np.array(Image.open(p).convert('RGBA'))
    white=f[...,:3].min(axis=2)>225
    lab,_=ndimage.label(white); edge=np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])); edge=edge[edge>0]
    bg=ndimage.binary_dilation(np.isin(lab,edge),iterations=1)&(f[...,:3].min(axis=2)>200)
    f[...,3]=np.where(bg,0,255); return Image.fromarray(f)
def fit(gen, orig_path, out):
    orig=Image.open(orig_path).convert('RGBA'); ob=orig.split()[-1].point(lambda v:255 if v>60 else 0).getbbox()
    g=cut(gen); g=g.crop(g.getbbox())
    w,h=ob[2]-ob[0],ob[3]-ob[1]; s=min(w/g.width,h/g.height); g=g.resize((int(g.width*s),int(g.height*s)),Image.LANCZOS)
    c=Image.new('RGBA',orig.size,(0,0,0,0)); c.paste(g,(ob[0]+(w-g.width)//2,ob[1]+(h-g.height)//2),g); c.save(out)
if __name__=='__main__': fit(*sys.argv[1:4])
