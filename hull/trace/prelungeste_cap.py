# The arm carried on past its head (asked: the band longer at the head end by 2 more ribs parallel to _49, the rest to match): the
# head rib copied NV times along X towards the ship's middle every PAS m (parallel planes); the green lines and the lips' two head
# ends carried on straight along X to the new end; the band and the arm's surface given a straight strip from their head edge to the
# new end. Right arm computed, the left one mirrored. Writes guides (+ the new ribs _50, _51 ...), band, piece.
# Usage: python prelungeste_cap.py <guides npz> <band npz (v,f; left arm)> <piece npz> <out guides> <out band> <out piece> ; env PAS=40 NV=2
import sys, os, numpy as np, trimesh
G = dict(np.load(sys.argv[1])); Bd = np.load(sys.argv[2]); Z = np.load(sys.argv[3]); OG, OB, OP = sys.argv[4:7]
PAS, NV = float(os.environ.get("PAS", "40")), int(os.environ.get("NV", "2")); L_ = PAS * NV; HK = "sectiune_brat_fata_D_49"
H = G[HK]; X0 = float(H[:, 0].mean()); dirx = -np.sign(X0)                 # (towards the ship's middle)
step = lambda n: np.outer(np.arange(n, 0, -1) * (L_ / n), [dirx, 0, 0])   # (offsets from the far end back to the head)
def ext_start(L):                                                          # a line whose start is at the head: carried on before it
    n = int(L_ // 2); return np.vstack([L[0] + step(n), L])
for k in ("spinare", "contur_exterior", "contur_interior"):
    G["%s_brat_fata_D" % k] = ext_start(G["%s_brat_fata_D" % k])
BZ = G["buze_gura_brat_fata_D"]; n = int(L_ // 2); G["buze_gura_brat_fata_D"] = np.vstack([BZ[0] + step(n), BZ, (BZ[-1] + step(n))[::-1]])
for i in range(NV):
    G["sectiune_brat_fata_D_%02d" % (50 + i)] = H + np.array([dirx * PAS * (i + 1), 0, 0])
for k in [k for k in G if k.endswith("_S") or "_S_" in k]:
    if not k.startswith("nacela") and "nacela" not in k: G.pop(k)
for k in list(G):
    if (k.endswith("_D") or "_D_" in k) and "nacela" not in k and not k.startswith("_"): G[k.replace("_D", "_S")] = G[k] * [-1, 1, 1]
np.savez(OG, **G)
# band: a strip of straight rows (exterior -> spine -> interior) from the head to the new end
E0, S0, I0 = (G["%s_brat_fata_D" % k][n] for k in ("contur_exterior", "spinare", "contur_interior"))   # (the head points)
NB = 17; rows = []
for t in np.linspace(0, L_, n + 1):
    o = np.array([dirx * t, 0, 0]); rows.append(np.vstack([np.linspace(E0 + o, S0 + o, NB // 2 + 1)[:-1], np.linspace(S0 + o, I0 + o, NB // 2 + 1)]))
R = np.array(rows); m_ = R.shape[1]; Vb = R.reshape(-1, 3); Fb = []
for r in range(len(R) - 1):
    for j in range(m_ - 1):
        q = [r * m_ + j, r * m_ + j + 1, (r + 1) * m_ + j + 1, (r + 1) * m_ + j]; Fb += [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]
VD, FD = Bd["v"] * [-1, 1, 1], Bd["f"][:, ::-1]                            # (the band file is the left arm)
V2 = np.vstack([VD, Vb]); F2 = np.vstack([FD, np.array(Fb) + len(VD)])
np.savez(OB, v=V2 * [-1, 1, 1], f=F2[:, ::-1])
# piece: its head edge (free edges in the head's plane, as one chain) extruded along X to the new end
V, F = Z["brat_fata_D__v"], Z["brat_fata_D__f"]; m = trimesh.Trimesh(V, F, process=False)
ed, cn = np.unique(m.edges_sorted, axis=0, return_counts=True); be = ed[cn == 1]
inh = np.abs(V[:, 0] - X0) < 0.6; be = be[inh[be[:, 0]] & inh[be[:, 1]]]
nb = {}
for a, b in be: nb.setdefault(a, []).append(b); nb.setdefault(b, []).append(a)
ends = [v for v, l in nb.items() if len(l) == 1]; ch = [ends[0] if ends else be[0][0]]; prev = None
while True:
    nx = [q for q in nb[ch[-1]] if q != prev]; prev = ch[-1]
    if not nx or nx[0] == ch[0]: break
    ch.append(nx[0])
ch = np.array(ch); k_ = len(ch); Vn = [V]; Fn = [F]; base = len(V); prev_idx = ch
for r in range(1, n + 1):
    Vn.append(V[ch] + np.array([dirx * L_ * r / n, 0, 0])); cur = base + (r - 1) * k_ + np.arange(k_)
    for j in range(k_ - 1):
        a, b, c, d = prev_idx[j], prev_idx[j + 1], cur[j + 1], cur[j]; Fn.append(np.array([[a, b, c], [a, c, d]]))
    prev_idx = cur
V3 = np.vstack(Vn); F3 = np.vstack(Fn); t3 = trimesh.Trimesh(V3, F3, process=False); trimesh.repair.fix_normals(t3)
cn3 = np.unique(t3.edges_sorted, axis=0, return_counts=True)[1]
np.savez(OP, brat_fata_D__v=t3.vertices, brat_fata_D__f=t3.faces, brat_fata_S__v=t3.vertices * [-1, 1, 1], brat_fata_S__f=t3.faces[:, ::-1])
print("PRELUNGIT cu %d vertebre la %.0f m (capatul nou la x %.1f): liniile +%.0f m, banda +%d randuri, piesa +%d randuri pe marginea capului de %d "
      "varfuri; ne-manifold %d" % (NV, PAS, X0 + dirx * L_, L_, n, n, k_, int((cn3 > 2).sum())))
