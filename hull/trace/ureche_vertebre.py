# The old ear's ribs turned into vertebrae (asked: the ear's margin outline is fine, but its ribs should be vertebrae, not
# full circles): each rib loop kept only past the body's widest point at its y (the new PS + the right back arm; XG m
# extra) - the longest run there, one open arc per rib (the ear's own section), right side.
# Usage: python ureche_vertebre.py <ear guides npz (contur_margine_D, coasta_*)> <body npz (gp_PS, gp_brat_spate_D)> <body dx> <out.npz>
import sys, numpy as np, igl
G = np.load(sys.argv[1]); B = np.load(sys.argv[2]); DX = float(sys.argv[3]); OUT = sys.argv[4]
Vs, Fs, o = [], [], 0
for n in ("gp_PS", "gp_brat_spate_D"):
    v = B[n + "__v"] + [DX, 0, 0]; f = B[n + "__f"]; Vs.append(v); Fs.append(f + o); o += len(v)
V = np.vstack(Vs); F = np.vstack(Fs).astype(np.int64)
import trimesh, os; TM = trimesh.Trimesh(V, F, process=False); XG = float(os.environ.get("XG", "0"))
out = {"contur_margine_D": G["sep_contur_margine_D"]}; rep = []
for k in sorted(q for q in G.files if q.startswith("sep_coasta")):
    P = G[k]; closed = np.allclose(P[0], P[-1]); P = P[:-1] if closed else P
    if not k.endswith("_D"): P = P if P[:, 0].max() > 0 else P                       # the full PS ribs: their right half only
    y0 = float(np.median(P[:, 1])); sec = TM.section(plane_origin=[0, y0, 0], plane_normal=[0, 1, 0])
    xo = max(q[:, 0].max() for q in sec.discrete) if sec is not None else 0.0            # the body's widest point at that y
    outside = P[:, 0] > xo + XG                                                          # the ear = what sticks out past it
    if not outside.any(): continue
    n = len(P); best = (0, 0); i = 0
    idx = np.r_[np.arange(n), np.arange(n)]; run = 0; start = 0                          # the longest cyclic run outside
    for j in range(2 * n):
        if outside[idx[j]]: run += 1; start = j - run + 1 if run == 1 else start
        else: run = 0
        if run > best[0] and run <= n: best = (run, start)
    L, s0 = best; arc = P[idx[s0:s0 + L]]
    nm = "vertebra_" + k.replace("sep_coasta_", "").replace("_D", "") + "_D"; out[nm] = arc
    rep.append("%s: %d puncte din %d, de la corp (x %.0f) (y %.0f, x %.0f..%.0f, z %.0f..%.0f)" % (nm, L, n, xo, arc[:, 1].mean(), arc[:, 0].min(), arc[:, 0].max(), arc[:, 2].min(), arc[:, 2].max()))
print("VERTEBRE URECHE D: %d (din coastele vechi, doar arcul din afara corpului nou)" % (len(out) - 1))
for r in rep: print("   " + r)
np.savez(OUT, **out)
