# The front arm's surface rebuilt on the cleaned guides (asked: guides separately with clean lines, then the surfaces): (1) every
# vertex put on the guides' own model with piesa_pe_model.py (per section an ellipse, major axis exterior -> interior of the CLEAN
# contours, through the clean lips along the mouth, minor radius from the ribs; fades out from rib SECT_A, the lobe from SECT_B
# untouched); (2) the open rim at the nacelle mouth snapped back onto the clean nacelle contours capat1 / capat2 (as
# margine_pe_contur.py did on the old ones: rim vertices within MAXD m moved onto the curve, the move spread over R m so no
# crease). Topology unchanged (same vertices / faces as the atelier arm). Left arm = exact mirror later.
# Usage: python brat_pe_ghidaje_curate.py <clean guides npz> <out npz> ; env SECT_A=38 SECT_B=41 MAXD=3 R=10 ENDS=8
import sys, os, subprocess, numpy as np, tempfile
from scipy.spatial import cKDTree
G = np.load(sys.argv[1], allow_pickle=True); OUT = sys.argv[2]; E = lambda k, d: float(os.environ.get(k, d)); MAXD, R = E("MAXD", 3), E("R", 10)
V = G["at_brat_fata_S__v"].astype(float); F = list(G["at_brat_fata_S__f"]); TRI = np.array([[f[0], f[i], f[i + 1]] for f in F for i in range(1, len(f) - 1)])
mx = np.array([-1, 1, 1]); td = tempfile.mkdtemp(); gin, pin, pout = [os.path.join(td, n) for n in ("g.npz", "p.npz", "o.npz")]
GD = {}
for k in G.files:
    if k.startswith("g_as_bf_") and not k.startswith("g_as_bf_sectiune"): GD[k[8:].replace("_brat_fata_S", "_brat_fata_D")] = G[k] * mx
    if k.startswith("g_as_bf_sectiune_brat_fata_S_"): GD["sectiune_brat_fata_D_" + k.split("_")[-1]] = G[k] * mx
np.savez(gin, **GD); np.savez(pin, brat_fata_D__v=V * mx, brat_fata_D__f=TRI[:, ::-1])
r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "piesa_pe_model.py"), gin, pin, pout], capture_output=True, text=True, env=dict(os.environ))
print(r.stdout.strip(), r.stderr.strip()[-500:])
V1 = np.load(pout)["brat_fata_D__v"] * mx
# open rim = edges used by one face
from collections import Counter
ec = Counter(tuple(sorted((f[i], f[(i + 1) % len(f)]))) for f in F for i in range(len(f))); rim = np.array(sorted({v for e, c in ec.items() if c == 1 for v in e}))
def dense(P, h=.1):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; u = np.arange(0, d[-1], h); return np.c_[[np.interp(u, d, P[:, k]) for k in range(3)]].T
ENDS = E("ENDS", 8); CL = [dense(G["g_as_nac_contur_nacela_capat1_S"]), dense(G["g_as_nac_contur_nacela_capat2_S"])]   # (ENDS m at each curve end left alone)
C = np.r_[CL[0], CL[1]]; endm = np.r_[[np.minimum(np.arange(len(c)), len(c) - 1 - np.arange(len(c))) * .1 for c in CL]].ravel() if False else np.concatenate([np.minimum(np.arange(len(c)), len(c) - 1 - np.arange(len(c))) * .1 for c in CL]); kc = cKDTree(C)
d, j = kc.query(V1[rim]); sel = (d < MAXD) & (endm[j] > ENDS); R_ = rim[sel]; DISP = C[j[sel]] - V1[R_]
krim = cKDTree(V1[R_]); dd, jj = krim.query(V1, k=8, distance_upper_bound=R)
W = np.where(np.isfinite(dd), (1 - np.minimum(dd, R) / R) ** 2, 0); W[np.isinf(dd)] = 0; jj = np.where(np.isfinite(dd), jj, 0)
mv = (W[..., None] * DISP[jj]).sum(1) / np.maximum(W.sum(1), 1e-9)[:, None]; w0 = np.max(W, axis=1); V2 = V1 + mv * np.clip(w0, 0, 1)[:, None]
V2[R_] = C[j[sel]]
mv1, mv2 = np.linalg.norm(V1 - V, axis=1), np.linalg.norm(V2 - V, axis=1)
kv = cKDTree(V2); rep = []
for k in ("g_as_bf_contur_exterior_brat_fata_S", "g_as_bf_buze_gura_brat_fata_S", "g_as_nac_contur_nacela_capat1_S", "g_as_nac_contur_nacela_capat2_S"):
    rep.append("%s %.2f" % (k[5:], kv.query(G[k])[0].max()))
np.savez(OUT, at_brat_fata_S__v=V2, at_brat_fata_S__f=G["at_brat_fata_S__f"])
print("BRAT pe model: mutat medie %.2f max %.2f m; gura lipita pe contururile nacelei: %d varfuri de margine (max %.2f m), dupa: medie %.2f max %.2f m; ghidaje pe piesa max: %s" % (mv1.mean(), mv1.max(), sel.sum(), d[sel].max(), mv2.mean(), mv2.max(), "; ".join(rep)))
