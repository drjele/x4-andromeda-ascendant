# Blade guides that START at hinge 7 and stow by ONE turn (asked: no slide - leave room for the other blades; the blade starts at 7,
# a single rotation, maybe a smoother curve). Built in the STOWED place: along the front arm's spine (g_as_bf_spinare_brat_fata_S)
# from the spine point at hinge 7 for LEN m - the wide side of the lying V on the spine, the sharp apex W m across the arm towards the
# U's inside, open OPEN x W up / down, narrowing to the tip over the last TAPER m (rounded start), all Gaussian-smoothed SIG m (clean,
# smoother than before: the arm's own curve). The deployed blade = these guides turned ANG deg about the vertical through hinge 7.
# Writes <out>.npz (deployed: lama_varf, lama_margine_sus / _jos, lama_nervura_NN, lama_radacina; +_D) and <out>_strans.npz (stowed).
# HX, HY: the hinge (default point 7: -59.6, 74.3) - the blade still starts on the spine at the point nearest to it; DZ: the whole blade
# lowered DZ m (along -thickness, inside the arm) so it leaves the arm under the nacelle (asked).
# Usage: blender -b <scene> --python ghid_lama4.py -- <out.npz> ; env LEN=750 W=45.2 OPEN=0.3 TAPER=252 SIG=20 ANG=<deg> PAS=60 GX=3100 HX HY DZ=0
import bpy, sys, os, json, math, numpy as np
from mathutils.kdtree import KDTree
OUT = sys.argv[sys.argv.index("--") + 1]; E = lambda k, d: float(os.environ.get(k, d)); GX = E("GX", 3100)
LEN, W, OPEN, TAPER, SIG, ANG, PAS = E("LEN", 750), E("W", 45.2), E("OPEN", .3), E("TAPER", 252), E("SIG", 20), E("ANG", 0), E("PAS", 60)
o = bpy.data.objects["g_as_bf_sudat_S"]; L_ = json.loads(o["linii"])
def line(nm):
    P = np.array([o.matrix_world @ p.co.xyz for p in o.data.splines[L_.index(nm)].points]) + [GX, 0, 0]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; u = np.arange(0, d[-1], 1.0); return np.c_[[np.interp(u, d, P[:, k]) for k in range(3)]].T
Sp, Ci = line("g_as_bf_spinare_brat_fata_S"), line("g_as_bf_contur_interior_brat_fata_S")
H = np.array([E("HX", -59.6), E("HY", 74.3)]); i0 = int(np.argmin(np.linalg.norm(Sp[:, :2] - H, axis=1))); s = np.arange(i0, min(i0 + int(LEN) + 1, len(Sp)))
def gsm(A, sig):
    r = int(3 * sig); k = np.exp(-.5 * (np.arange(-r, r + 1) / sig) ** 2); k /= k.sum()
    P = np.r_[2 * A[0] - A[r:0:-1], A, 2 * A[-1] - A[-2:-r - 2:-1]]; return np.c_[[np.convolve(P[:, j], k, mode="valid") for j in range(A.shape[1])]].T
base = gsm(Sp[s], SIG); T = np.gradient(base, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
kc = KDTree(len(Ci))
for j, p in enumerate(Ci): kc.insert(p, j)
kc.balance()
U = np.array([np.array(kc.find(p)[0]) - p for p in base]); U -= T * (U * T).sum(1)[:, None]; U = gsm(U / np.linalg.norm(U, axis=1)[:, None], SIG); U /= np.linalg.norm(U, axis=1)[:, None]
N = np.cross(T, U); N /= np.linalg.norm(N, axis=1)[:, None]; N[N[:, 2] < 0] *= -1
t = np.arange(len(s), dtype=float); Lb = t[-1]; k_ = 20.0; w = W * np.clip(1 - np.logaddexp(0, (t - (Lb - TAPER)) / k_) * k_ / TAPER, 0, 1)
base = base - N * E("DZ", 0)
Va = base + U * w[:, None]; Ms = base + N * (OPEN * w / 2)[:, None]; Mj = base - N * (OPEN * w / 2)[:, None]
def pack(Va, Ms, Mj):
    G = {"varf": Va, "margine_sus": Ms, "margine_jos": Mj, "radacina": np.r_[Ms[:1], Va[:1], Mj[:1]]}
    for k, sk in enumerate(np.arange(PAS, Lb - 5, PAS)):
        j = int(sk); G["nervura_%02d" % k] = np.r_[Ms[j:j + 1], Va[j:j + 1], Mj[j:j + 1]]
    out = {}
    for k, v in G.items(): out["lama_" + k] = v; out["lama_" + k + "_D"] = v * [-1, 1, 1]
    return out
hz = base[0, 2]; c, sn = math.cos(math.radians(ANG)), math.sin(math.radians(ANG))
rot = lambda P: np.c_[H[0] + c * (P[:, 0] - H[0]) - sn * (P[:, 1] - H[1]), H[1] + sn * (P[:, 0] - H[0]) + c * (P[:, 1] - H[1]), P[:, 2]]
np.savez(OUT.replace(".npz", "_strans.npz"), **pack(Va, Ms, Mj)); np.savez(OUT, **pack(rot(Va), rot(Ms), rot(Mj)))
np.savez(OUT.replace(".npz", "_param.npz"), hinge=np.r_[H, hz], ang=ANG, base=base, U=U, N=N, T=T)
print("LAMA4: balama (%.1f, %.1f), radacina la %s (coborata %.1f m), %d m pe spinare, latime %.1f, deschidere %.1f; deschisa = rotita %+.1f grade" % (H[0], H[1], base[0].round(1), E("DZ", 0), Lb, W, OPEN * W, ANG))
