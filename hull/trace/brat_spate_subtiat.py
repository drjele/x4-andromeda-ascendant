# The back arms made thinner (asked: the back arms' default diameter -15%, the rest adjusted, the bend and the joint with the PS
# kept): every vertex of the arm pulled towards its spine (place across the section scaled by f(s)), f = 1 at the PS wall (s = 0) and
# easing (quintic) to FACTOR over TRECERE m - so the joint stays and the spine (the bend) is untouched. Attached pieces (ears,
# small ears) follow: each vertex moved like its nearest arm vertices (inverse-square over K), faded out at FADE m from the arm.
# Usage: python brat_spate_subtiat.py <oval guides npz> <in npz: arm_D, arm_S + attached <name>_D/_S (v,f each as <k>__v/<k>__f)> <out npz>
#        env FACTOR=0.85 TRECERE=150 FADE=40 K=8
import sys, os, numpy as np
from scipy.spatial import cKDTree
G = np.load(sys.argv[1]); Z = dict(np.load(sys.argv[2])); OUT = sys.argv[3]; e = lambda k, d: float(os.environ.get(k, d))
FA, TR, FD, K = e("FACTOR", "0.85"), e("TRECERE", "150"), e("FADE", "40"), int(e("K", "8"))
sm5 = lambda x: x ** 3 * (10 - 15 * x + 6 * x * x); arclen = lambda L: np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
out = {}
for sd, sg in (("D", 1), ("S", -1)):
    SP = G["spinare_brat_D"] * [sg, 1, 1]; dS = arclen(SP); TS = np.gradient(SP, axis=0); TS /= np.linalg.norm(TS, axis=1)[:, None]
    V = Z["brat_spate_%s__v" % sd]; kd = cKDTree(SP); j = kd.query(V)[1]
    s = np.clip(dS[j] + np.einsum("ij,ij->i", V - SP[j], TS[j]), 0, None)
    P = SP[j] + TS[j] * (s - dS[j])[:, None]; off = V - P; f = 1 - (1 - FA) * sm5(np.clip(s / TR, 0, 1))
    V2 = P + off * f[:, None]; D_ = V2 - V; out["brat_spate_%s__v" % sd] = V2
    ka = cKDTree(V); mv = np.linalg.norm(D_, axis=1)
    for k in [k[:-3] for k in Z if k.endswith("_%s__v" % sd) and not k.startswith("brat_spate")]:
        W = Z[k + "__v"]; d, i = ka.query(W, K); w = 1 / np.maximum(d, 0.5) ** 2; w /= w.sum(1)[:, None]
        fade = np.clip(1 - d[:, 0] / FD, 0, 1); fade = fade * fade * (3 - 2 * fade)
        out[k + "__v"] = W + np.einsum("ij,ijk->ik", w, D_[i]) * fade[:, None]
        print("  %s urmeaza bratul: mutat max %.2f m" % (k, np.linalg.norm(out[k + "__v"] - W, axis=1).max()))
    r0 = np.linalg.norm(off, axis=1); print("BRAT spate %s: grosimea x%.2f de la %.0f m de perete; mutat max %.2f m; la perete (s<5) max %.3f m" % (
        sd, FA, TR, mv.max(), mv[s < 5].max() if (s < 5).any() else 0))
np.savez(OUT, **out)
