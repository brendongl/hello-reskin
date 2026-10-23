import pickle,sys
def nodes(v): return {int(x['rid']):x['data'] for x in v['references']['RefIds']}
def walk(N,rid,depth,acc,path=''):
    n=N[rid]; g=n.get('Geometries') or []; nv=sum(len(x['Vertices']) for x in g)
    nm=n['Name']; p=path+'/'+nm
    acc.append((depth,nm,len(g),nv,n.get('SettingIndexes'),n.get('BaseColor',{}).get('rgba'),p))
    for c in n.get('Children') or []: walk(N,int(c['rid']),depth+1,acc,p)
if __name__=='__main__':
    for k,v in pickle.load(open('export/svgfiles.pkl','rb')).items():
        acc=[]; walk(nodes(v),v['rootNode']['rid'],0,acc)
        with open(f"export/svgtree_{k[1]}.txt",'w') as f:
            for d,nm,g,nv,s,c,p in acc: f.write('  '*d+f"{nm} g={g} v={nv} set={s} col={c:08x}\n")
        print(k[1], len(acc),'nodes', sum(a[3] for a in acc),'verts')
