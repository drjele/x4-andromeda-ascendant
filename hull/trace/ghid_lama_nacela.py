# Blade guides variant "after the nacelle" (asked: the battle blades come out of the red nacelles through their thin edge; try both
# blade shapes; they slide out). The blade's wide side sits on the nacelle's thin edge (g_as_nac_contur_nacela_varf_S), open up and
# down OPEN x its depth across the nacelle (lip to lip direction); its sharp apex goes out along the nacelle's V axis (lips middle ->
# thin edge) K x the nacelle's own depth at that place - so, slid back by that much, the whole blade fits inside the nacelle. Lines,
# directions and depth Gaussian-smoothed SIG m (clean lines). Same keys as ghid_lama3.py: lama_varf, lama_margine_sus / _jos,
# lama_nervura_NN, lama_radacina (+ _D); <out>_param.npz: the slide vector per station (dir x depth) for the retracted state.
# Usage: blender -b <scene> --python ghid_lama_nacela.py -- <out.npz> ; env K=0.9 OPEN=0.3 SIG=20 PAS=60 GX=3100
import bpy, sys, os, json, numpy as np
OUT = sys.argv[sys.argv.index("--") + 1]; E = lambda k, d: float(os.environ.get(k, d)); GX = E("GX", 3100)
K, OPEN, SIG, PAS = E("K", .9), E("OPEN", .3), E("SIG", 20), E("PAS", 60)
o = bpy.data.objects["g_as_nac_sudat_S"]; names = json.loads(o["linii"])
def line(nm): return np.array([o.matrix_world @ p.co.xyz for p in o.data.splines[names.index(nm)].points]) + [GX, 0, 0]
v, a, b = line("g_as_nac_contur_nacela_varf_S"), line("g_as_nac_contur_nacela_capat1_S"), line("g_as_nac_contur_nacela_capat2_S")
d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(v, axis=0), axis=1))]; u = np.arange(0, d[-1], 1.0)
rs = lambda P: np.c_[[np.interp(u, d, P[:, k]) for k in range(3)]].T; v, a, b = rs(v), rs(a), rs(b)
def gsm(A, sig):
    r = int(3 * sig); k = np.exp(-.5 * (np.arange(-r, r + 1) / sig) ** 2); k /= k.sum()
    P = np.r_[2 * A[0] - A[r:0:-1], A, 2 * A[-1] - A[-2:-r - 2:-1]]
    return np.c_[[np.convolve(P[:, j], k, mode="valid") for j in range(A.shape[1])]].T
mid = (a + b) / 2; ax = v - mid; dep = np.linalg.norm(ax, axis=1); ax /= np.maximum(dep, 1e-6)[:, None]
nv = b - a; nv /= np.maximum(np.linalg.norm(nv, axis=1), 1e-6)[:, None]
v = gsm(v, SIG); ax = gsm(ax, SIG); nv = gsm(nv, SIG); dep = gsm(dep[:, None], SIG)[:, 0]
T = np.gradient(v, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
ax -= T * (ax * T).sum(1)[:, None]; ax /= np.linalg.norm(ax, axis=1)[:, None]; nv -= T * (nv * T).sum(1)[:, None] + ax * (nv * ax).sum(1)[:, None]; nv /= np.linalg.norm(nv, axis=1)[:, None]
if nv[:, 2].mean() < 0: nv = -nv
db = K * dep                                                                  # the blade's depth (wide side -> apex)
Va = v + ax * db[:, None]; Ms = v + nv * (OPEN * db / 2)[:, None]; Mj = v - nv * (OPEN * db / 2)[:, None]
def quality(P):
    dd = np.diff(P, axis=0); L_ = np.linalg.norm(dd, axis=1); dd /= np.maximum(L_, 1e-9)[:, None]
    return (np.degrees(np.arccos(np.clip((dd[1:] * dd[:-1]).sum(1), -1, 1))) / np.maximum(L_[1:], 1e-6) * .5).max()
L = u[-1]
print("LAMA DUPA NACELA: %.0f m pe muchia subtire a nacelei, adancime %.1f -> 0 m (%.2f x nacela), deschidere %.1f m la radacina; frangeri max: varf %.2f, margini %.2f / %.2f grade/0,5 m"
      % (L, db[0], K, OPEN * db[0], quality(Va), quality(Ms), quality(Mj)))
G = {"varf": Va, "margine_sus": Ms, "margine_jos": Mj, "radacina": np.r_[Ms[:1], Va[:1], Mj[:1]]}
for k_, sk in enumerate(np.arange(PAS, L - 5, PAS)):
    j = int(sk); G["nervura_%02d" % k_] = np.r_[Ms[j:j + 1], Va[j:j + 1], Mj[j:j + 1]]
out = {}
for k_, val in G.items(): out["lama_" + k_] = val; out["lama_" + k_ + "_D"] = val * [-1, 1, 1]
np.savez(OUT, **out); np.savez(OUT.replace(".npz", "_param.npz"), slide=-ax * db[:, None], axis=ax, depth=db, thin_edge=v)
