# Blade guides that follow the front arm (asked: the blade guides must follow the curve / contour of g_as_bf_sudat_S and
# g_as_nac_sudat_S, and be shown apart to be seen well). Base line = the arm's inner contour (g_as_bf_contur_interior_brat_fata_S,
# continuous along the whole arm; the nacelle tip line runs along it); per station the direction from the arm spine to that
# contour, turned into the arm's cross plane (the U's inside); outer edge = contour + D along it, inner edge = + D + w, with D the
# reference blade's median distance (Circle.007) and w = W0 then falling linearly to 0 over the last TAPER m to the tip. The blade's
# extent = the stations the reference blade covers. Thickness direction = the cross of the line and that offset (for the piece).
# 3D and sharp (asked: like g_as_nac_sudat_S, flatter): a rhomb section - the two edges sharp, a top ridge H_SUS x width and a bottom
# ridge H_JOS x width off the middle line along the thickness direction; ribs = closed rhombs every PAS m; all closes to the tip.
# Writes <out.npz>: lama_margine_exterioara / _interioara, lama_mijloc, lama_varf_sus / _jos, lama_nervura_NN, lama_taietura_radacina, lama_balama (+ _D).
# Usage: blender -b <scene> --python ghid_lama2.py -- <out.npz> ; env W0=45.2 TAPER=252 PAS=60 D=<median> GX=3100 H_SUS=0.25 H_JOS=0.1
import bpy, sys, os, json, numpy as np
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; E = lambda k, d: float(os.environ.get(k, d)); GX = E("GX", 3100)
def line(W, nm):
    o = bpy.data.objects[W]; sp = o.data.splines[json.loads(o["linii"]).index(nm)]
    return np.array([o.matrix_world @ p.co.xyz for p in sp.points]) + [GX, 0, 0]
def res(P, step=1.0):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; u = np.arange(0, d[-1], step); return np.c_[[np.interp(u, d, P[:, k]) for k in range(3)]].T
Ci = res(line("g_as_bf_sudat_S", "g_as_bf_contur_interior_brat_fata_S")); Sp = res(line("g_as_bf_sudat_S", "g_as_bf_spinare_brat_fata_S"))
Nv = res(line("g_as_nac_sudat_S", "g_as_nac_contur_nacela_varf_S"))
ref = bpy.data.objects["Circle.007"]; R = np.array([ref.matrix_world @ v.co for v in ref.data.vertices]); R = R[R[:, 0] < 0]
T = np.gradient(Ci, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
from mathutils.kdtree import KDTree
ks = KDTree(len(Sp))
for i, p in enumerate(Sp): ks.insert(p, i)
ks.balance()
U = np.zeros_like(Ci)
for i, p in enumerate(Ci):
    q = np.array(ks.find(p)[0]); u = p - q; u -= T[i] * (u @ T[i]); U[i] = u / np.linalg.norm(u)
k = int(E("SM", 15)); Uk = np.array([U[max(0, i - k):i + k + 1].mean(0) for i in range(len(U))]); U = Uk / np.linalg.norm(Uk, axis=1)[:, None]
# reference blade: per contour station, its distance along U (outer edge = the nearest)
kc = KDTree(len(Ci))
for i, p in enumerate(Ci): kc.insert(p, i)
kc.balance()
idx = np.array([kc.find(p)[1] for p in R]); dd = np.array([(p - Ci[i]) @ U[i] for p, i in zip(R, idx)])
i0, i1 = idx.min(), idx.max(); D = E("D", np.median([dd[idx == i].min() for i in np.unique(idx)]))
W0, TAPER, PAS = E("W0", 45.2), E("TAPER", 252), E("PAS", 60)
s = np.arange(i0, i1 + 1); L = len(s) - 1; w = np.where(s - i0 <= L - TAPER, W0, W0 * np.clip((i1 - s) / TAPER, 0, 1))
Eo = Ci[s] + U[s] * D; Ei = Ci[s] + U[s] * (D + w[:, None] if False else (D + w)[:, None]); M = (Eo + Ei) / 2
dn = np.array([np.min(np.linalg.norm(Nv - p, axis=1)) for p in Eo[::10]])
print("LAMA dupa brat: statii %d..%d pe conturul interior (%d m), D %.1f m de contur, latime %.1f m (vartful pe ultimii %.0f m); marginea ext. fata de varful nacelei: %.1f .. %.1f m"
      % (i0, i1, L, D, W0, TAPER, dn.min(), dn.max()))
Nt = np.cross(T[s], U[s]); Nt /= np.linalg.norm(Nt, axis=1)[:, None]; Nt[Nt[:, 2] < 0] *= -1     # the blade's thickness direction, up
HS, HJ = E("H_SUS", .25), E("H_JOS", .1)                                 # 3D and sharp (asked): a flattened nacelle-like V both ways -> a rhomb section
Vs = M + Nt * (HS * w)[:, None]; Vj = M - Nt * (HJ * w)[:, None]
print("SECTIUNE romb: varful de sus iese %.2f x latimea (%.1f m), cel de jos %.2f x (%.1f m); margini ascutite" % (HS, HS * W0, HJ, HJ * W0))
G = {"mijloc": M, "margine_exterioara": Eo, "margine_interioara": Ei, "varf_sus": Vs, "varf_jos": Vj, "taietura_radacina": np.r_[Ei[:1], Vs[:1], Eo[:1], Vj[:1], Ei[:1]]}
for kk, sk in enumerate(np.arange(PAS, L - 5, PAS)):
    j = int(sk); G["nervura_%02d" % kk] = np.r_[Ei[j:j + 1], Vs[j:j + 1], Eo[j:j + 1], Vj[j:j + 1], Ei[j:j + 1]]
G["balama"] = np.r_[M[:1] - Nt[:1] * 16, M[:1] + Nt[:1] * 16]
G2 = {}
for kk, v in G.items(): G2["lama_" + kk] = v; G2["lama_" + kk + "_D"] = v * [-1, 1, 1]
np.savez(OUT, **G2); np.savez(OUT.replace(".npz", "_param.npz"), D=D, W0=W0, TAPER=TAPER, i0=i0, i1=i1, U=U[s], T=T[s], base=Ci[s])
print("LAMA balama (radacina) la %s" % np.round(M[0], 1))
