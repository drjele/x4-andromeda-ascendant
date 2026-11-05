import numpy as np, sys
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components as cc
Z=np.load(sys.argv[1]); names=[str(n) for n in Z["names"]]
for n in sys.argv[2:]:
    k=n.replace(" ","_"); v,f=Z[k+"__v"],Z[k+"__f"]; key=np.round(v/0.01).astype(np.int64); _,inv=np.unique(key,axis=0,return_inverse=True); ff=inv.ravel()[f]
    a=np.concatenate([ff[:,0],ff[:,1]]);b=np.concatenate([ff[:,1],ff[:,2]]);N=inv.max()+1;nc,l=cc(coo_matrix((np.ones(len(a)),(a,b)),shape=(N,N)),directed=False); fl=l[ff[:,0]]
    print(n,"comps",nc)
    cnt=np.bincount(fl); 
    for c in np.argsort(-cnt)[:14]:
        V=v[f[fl==c].ravel()]; print("  ",cnt[c],"x%.0f..%.0f y%.0f..%.0f z%.0f..%.0f"%(V[:,0].min(),V[:,0].max(),V[:,1].min(),V[:,1].max(),V[:,2].min(),V[:,2].max()))
