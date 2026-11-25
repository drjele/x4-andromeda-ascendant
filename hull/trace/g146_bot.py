# nt_146 nose, asked 2026-11-07: rounded like the PS nose. Exact: A = tip R 35 + one arc + line into the 11-05 outer rail (body unchanged);
# B = the PS nose itself (tip R 35, cap R 190 to -82.7 deg, its straight side) + line + one fillet arc into the 11-05 rail. Writes <dir>/bot_seg.json + b1_bot_A_B.png. Usage: g146_bot.py <dir>/
import numpy as np, json, sys, g1_arce as g
VARF = float(__import__("os").environ.get("VARF", "452.5"))                      # asked 2026-11-08: PI tip where the PS tip is (468.5), the rest of the outline unchanged
seg=json.load(open("/home/adrian/Documents/Andromeda/2026-11-05-nt146/rails_seg.json"))["E"]
R0=dict(seg=seg,x0=np.array([0,452.5]),th0=0.0); P,u=g.draw(R0,.25); L=np.array([q[0] for q in seg]);K=np.array([q[1] for q in seg]); e=np.r_[0,np.cumsum(L)]
th=lambda s: np.interp(s, e, np.r_[0,np.cumsum(L*K)]) if False else (np.r_[0,np.cumsum(L*K)][np.clip(np.searchsorted(e,s,side='right')-1,0,len(L)-1)] + K[np.clip(np.searchsorted(e,s,side='right')-1,0,len(L)-1)]*(s-e[np.clip(np.searchsorted(e,s,side='right')-1,0,len(L)-1)]))
RT,TT=35.0,np.radians(34); te=np.array([RT*np.sin(TT),VARF-RT*(1-np.cos(TT))])
def build(s):
    h=float(th(s)); d=np.array([np.cos(h),np.sin(h)]); D=-TT-h  # turn amount (clockwise)
    # unit-radius clockwise arc from heading -TT by D
    a0=-TT; v=np.array([np.sin(a0)-np.sin(a0-D), -(np.cos(a0-D)-np.cos(a0))]) * -1
    v=np.array([(np.sin(a0-D)-np.sin(a0))/-1, (np.cos(a0)-np.cos(a0-D))/-1])
    p=P[np.argmin(abs(u-s))]; cr=lambda a,b:a[0]*b[1]-a[1]*b[0]; Rc=cr(p-te,d)/cr(v,d); ln=np.dot(p-(te+Rc*v),d); return h,D,Rc,ln,p
for s in []:
    h,D,Rc,ln,p=build(s)
    if Rc<=0 or ln<0: print(s,'imposibil',round(Rc),round(ln)); continue
    nseg=[(RT*TT,-1/RT),(Rc*D,-1/Rc)]+([(ln,0.0)] if ln>0.3 else []); 
    # rest of old chain from s
    j=np.searchsorted(e,s,side='right')-1; rest=[(e[j+1]-s,K[j])]+[(L[i],K[i]) for i in range(j+1,len(L))]
    N=dict(seg=nseg+rest,x0=np.array([0,VARF]),th0=0.0); Q,_=g.draw(N,.25)
    w=lambda A,dd: A[np.argmin(abs(A[:900*4,1]-(VARF-dd))),0]
    print("s %3d: cap R %.0f (%.0f m), dreapta %.0f, leaga la (%.0f,%.0f) dir %.0f | latimi d20 %.0f d50 %.0f d80 %.0f d120 %.0f d170 %.0f d250 %.0f (vechi %.0f %.0f %.0f %.0f %.0f %.0f)"%(s,Rc,Rc*D,ln,p[0],p[1],np.degrees(h),*[w(Q,dd) for dd in (20,50,80,120,170,250)],*[w(P,dd) for dd in (20,50,80,120,170,250)]))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
cr=lambda a,b:a[0]*b[1]-a[1]*b[0]
def uv(a0,D): return np.array([np.sin(a0)-np.sin(a0-D), np.cos(a0-D)-np.cos(a0)])
def rest_from(s):
    j=np.searchsorted(e,s,side='right')-1; return [(e[j+1]-s,K[j])]+[(L[i],K[i]) for i in range(j+1,len(L))]
# A: tip R35 + cap + line into the old rail at s=160
h,D,Rc,ln,p=build(160.0); A=[(RT*TT,-1/RT),(Rc*D,-1/Rc),(ln,0.0)]+rest_from(160.0)
# B: the PS nose itself (R35 + R190 to -82.7 deg), then line + fillet arc into the old rail at s
H=np.radians(82.7); Bh=[(RT*TT,-1/RT),(190*(H-TT),-1/190.)]; Q,_=g.draw(dict(seg=Bh,x0=np.array([0,VARF]),th0=0.0),.25); a=Q[-1]; d0=np.array([np.cos(-H),np.sin(-H)])
best=None; BS=float(__import__('os').environ.get('BOT_S','0'))
for s in np.arange(250,800,5.0):
    hs=float(th(s)); Df=-H-hs; p=P[np.argmin(abs(u-s))]; M=np.c_[d0, np.sign(Df)*uv(-H,Df)]
    if abs(Df)<1e-3: continue
    lnB,Rf=np.linalg.solve(M,p-a)
    if not BS and lnB>0 and Rf>150 and (best is None or abs(Df)<abs(best[3])): best=(s,lnB,Rf,Df)                     # the least extra turn: the PS side runs straight on into our rail
    if BS and lnB>0 and Rf>150 and abs(s-BS)<abs(best[0]-BS if best else 1e9): best=(s,lnB,Rf,Df)       # BOT_S: join where asked (the PS straight side carried on to there)
s,lnB,Rf,Df=best; print("B: leaga la s %.0f, dreapta %.0f, racord R %.0f (intoarcere %.1f gr)"%(s,lnB,Rf,np.degrees(Df)))
B=Bh+[(lnB,0.0),(Rf*abs(Df),-np.sign(Df)/Rf)]+rest_from(s)
print("A:", [(round(l),('R%.0f'%(1/abs(k)) if k else 'drept')) for l,k in A[:4]])
pc=np.load('/home/adrian/Documents/Andromeda/2026-10-29-imbinari/piese/ghid_rama_baza_v5_nas_ps.npz')['contur_rama_exterior']; sil=np.load('/home/adrian/Documents/Andromeda/2026-11-05-nt146/sil.npy')*[-1,1]
fig,ax=plt.subplots(1,2,figsize=(18,10))
for a_,lim in zip(ax,[(-20,560,-850,480),(-5,200,150,480)]):
    a_.plot(sil[:,0],sil[:,1],color='.75',lw=3,label='referinta 146')
    a_.plot(pc[:,0],pc[:,1]-(468.5-VARF),'k--',lw=1,label='PS (varful mutat pe al nostru)')
    a_.plot(P[:,0],P[:,1],'b',lw=1,label='vechi (11-05)')
    for nm,sg,c in (('A',A,'r'),('B',B,'g')):
        Z,_=g.draw(dict(seg=sg,x0=np.array([0,VARF]),th0=0.0),.25); a_.plot(Z[:,0],Z[:,1],c,lw=1.6,label=nm); np.save('%s/rail_%s.npy'%(sys.argv[1].rstrip('/'),nm),Z)
    a_.set_xlim(lim[0],lim[1]); a_.set_ylim(lim[2],lim[3]); a_.set_aspect('equal'); a_.grid(alpha=.3)
ax[0].legend(loc='lower left'); ax[1].set_title('botul: A = varf R35 + arc R%.0f + dreapta, corpul neschimbat;  B = botul PS (R35 + R190), corpul latit'%Rc)
fig.tight_layout(); fig.savefig(sys.argv[1]+'b1_bot_A_B.png',dpi=80)
json.dump({"A":A,"B":B},open(sys.argv[1]+'bot_seg.json','w'))
