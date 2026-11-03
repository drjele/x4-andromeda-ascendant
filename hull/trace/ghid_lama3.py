# Blade guides redrawn from zero (asked: of g_lamasep_lama_mijloc / _varf_jos one is extra; the section a LYING V with its sharp
# side at the back; keep the general shape). The general shape stays: the blade follows the front arm's inner contour
# (g_as_bf_contur_interior_brat_fata_S) at a constant distance D across the arm (direction spine -> contour, in the arm's cross
# plane), W wide, narrowing to its tip over the last TAPER m, over the stations the reference Circle.007 covers. Section = a lying V
# like the red nacelles (corrected): the wide open side towards the arm - two ends, one up and one down, OPEN x width apart - and
# the sharp apex W further, towards the front / the U's inside; all closing to 0 at the tip. Three lines only: lama_varf (the sharp edge),
# lama_margine_sus, lama_margine_jos; ribs lama_nervura_NN = V (sus -> varf -> jos) every PAS m; lama_radacina = the V at the root;
# lama_balama = the hinge on the WIDE side at the root (asked): the axis through the root ends of the two edges. D = mirror in x.
# Clean lines (asked): the arm-side base line and the across / thickness directions Gaussian-smoothed over SIG m (ends kept by
# reflection), the width going from constant to the taper through a rounded (softplus, ~BL m) start; prints the sharpest turn per 0.5 m and
# the curvature sign changes seen from above for each line, before / after.
# Usage: blender -b <scene> --python ghid_lama3.py -- <out.npz> ; env D=86.7 W=45.2 TAPER=252 OPEN=0.3 PAS=60 SM=15 GX=3100 SIG=0 BL=60
import bpy, sys, os, json, numpy as np
from mathutils.kdtree import KDTree
OUT = sys.argv[sys.argv.index("--") + 1]; E = lambda k, d: float(os.environ.get(k, d)); GX = E("GX", 3100)
D, W, TAPER, OPEN, PAS, SM = E("D", 86.7), E("W", 45.2), E("TAPER", 252), E("OPEN", .3), E("PAS", 60), int(E("SM", 15))
SIG, BL = E("SIG", 0), E("BL", 60)
def gsm(A, sig):
    if sig <= 0: return A
    r = int(3 * sig); k = np.exp(-.5 * (np.arange(-r, r + 1) / sig) ** 2); k /= k.sum()
    P = np.r_[2 * A[0] - A[r:0:-1], A, 2 * A[-1] - A[-2:-r - 2:-1]]          # odd reflection keeps the ends and their direction
    return np.c_[[np.convolve(P[:, j], k, mode='valid') for j in range(A.shape[1])]].T
def quality(P):
    d = np.diff(P, axis=0); L_ = np.linalg.norm(d, axis=1); d /= L_[:, None]
    ang = np.degrees(np.arccos(np.clip((d[1:] * d[:-1]).sum(1), -1, 1))) / np.maximum(L_[1:], 1e-6) * .5
    cz = np.cross(d[:-1, :2], d[1:, :2]); cz = cz[np.abs(cz) > 1e-5]
    return ang.max(), int((np.diff(np.sign(cz)) != 0).sum())
def line(obj, nm):
    o = bpy.data.objects[obj]; sp = o.data.splines[json.loads(o["linii"]).index(nm)]
    P = np.array([o.matrix_world @ p.co.xyz for p in sp.points]) + [GX, 0, 0]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; u = np.arange(0, d[-1], 1.0)
    return np.c_[[np.interp(u, d, P[:, k]) for k in range(3)]].T                      # 1 m steps
def kd(P):
    k = KDTree(len(P))
    for i, p in enumerate(P): k.insert(p, i)
    k.balance(); return k
C = line("g_as_bf_sudat_S", "g_as_bf_contur_interior_brat_fata_S"); Sp = kd(line("g_as_bf_sudat_S", "g_as_bf_spinare_brat_fata_S"))
T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
U = np.array([(lambda u: u - T[i] * (u @ T[i]))(C[i] - np.array(Sp.find(C[i])[0])) for i in range(len(C))])
U = np.array([U[max(0, i - SM):i + SM + 1].mean(0) for i in range(len(U))]); U /= np.linalg.norm(U, axis=1)[:, None]
N = np.cross(T, U); N /= np.linalg.norm(N, axis=1)[:, None]; N[N[:, 2] < 0] *= -1                # thickness direction, up
ref = bpy.data.objects["Circle.007"]; R = np.array([ref.matrix_world @ v.co for v in ref.data.vertices]); R = R[R[:, 0] < 0]
kc = kd(C); idx = np.array([kc.find(p)[1] for p in R]); i0, i1 = int(idx.min()), int(idx.max())
s = np.arange(i0, i1 + 1); L = float(i1 - i0); t = s - i0
w = np.where(t <= L - TAPER, W, W * np.clip((L - t) / TAPER, 0, 1))
if SIG > 0:                                                               # constant -> taper with a rounded start (softplus ramp, C1): no corner in the width
    k_ = BL / 3; r_ = np.logaddexp(0, (t - (L - TAPER)) / k_) * k_ / TAPER; w = W * np.clip(1 - r_, 0, 1)
arm = C[s] + U[s] * D                                                     # the wide open side, towards the arm
q0 = [quality(x_) for x_ in (arm, arm + U[s] * w[:, None])]
if SIG > 0:
    arm = gsm(arm, SIG); Tn = np.gradient(arm, axis=0); Tn /= np.linalg.norm(Tn, axis=1)[:, None]
    Us = gsm(U[s], SIG); Us -= Tn * (Us * Tn).sum(1)[:, None]; Us /= np.linalg.norm(Us, axis=1)[:, None]; U[s] = Us
    Ns = np.cross(Tn, Us); Ns /= np.linalg.norm(Ns, axis=1)[:, None]; Ns[Ns[:, 2] < 0] *= -1; N[s] = Ns
Va = arm + U[s] * w[:, None]                                              # the sharp apex, towards the front / the U's inside
Ms = arm + N[s] * (OPEN * w / 2)[:, None]; Mj = arm - N[s] * (OPEN * w / 2)[:, None]
print("LAMA V culcat: %d m, statii %d..%d pe conturul interior, la %.1f m de el; latime %.1f m, deschiderea V-ului %.1f m spre brat, varful ascutit spre fata (ca nacelele rosii)"
      % (L, i0, i1, D, W, OPEN * W))
print("   varful spre +U: componenta pe y medie %.2f (pozitiv = spre prova, +y)" % (U[s][:, 1]).mean())
hb = Ms[0] - Mj[0]; hb /= np.linalg.norm(hb)                              # the hinge on the wide side (asked): through the root ends of both edges
G = {"varf": Va, "margine_sus": Ms, "margine_jos": Mj, "radacina": np.r_[Ms[:1], Va[:1], Mj[:1]], "balama": np.r_[Mj[:1] - hb * 6, Ms[:1] + hb * 6]}
for nm_, P_ in (("varf", Va), ("margine_sus", Ms), ("margine_jos", Mj)):
    a_, c_ = quality(P_); print("CLEAN %-12s frangere max %.2f grade / 0,5 m, schimbari de sens (de sus) %d" % (nm_, a_, c_))
print("CLEAN inainte (fara netezire): baza %.2f grade / %d schimbari, varf %.2f / %d" % (q0[0][0], q0[0][1], q0[1][0], q0[1][1]))
for k, sk in enumerate(np.arange(PAS, L - 5, PAS)):
    j = int(sk); G["nervura_%02d" % k] = np.r_[Ms[j:j + 1], Va[j:j + 1], Mj[j:j + 1]]
out = {}
for k, v in G.items(): out["lama_" + k] = v; out["lama_" + k + "_D"] = v * [-1, 1, 1]
np.savez(OUT, **out); np.savez(OUT.replace(".npz", "_param.npz"), hinge_p=(Ms[0] + Mj[0]) / 2, hinge_dir=hb, D=D, W=W, TAPER=TAPER, OPEN=OPEN, i0=i0, i1=i1, T=T[s], U=U[s], N=N[s], base=C[s])
print("LAMA %d linii (S); balama pe partea lata: de la %s la %s" % (len(G), np.round(Mj[0], 1), np.round(Ms[0], 1)))
