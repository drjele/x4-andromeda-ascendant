# A reference decoration moved onto our surface (asked: R131 087_S migrated onto the hood): each vertex keeps its height above the
# reference surface under it (the nearest reference vertex not of the decoration, height along that point's normal turned upwards)
# and gets it above our surface (nearest point of our pieces to that reference point, normal turned the same way) + LIFT m.
# Usage: python decor_pe_suprafata.py <decor npz (v,f,tri_uv)> <reference surface npz (v,n)> <our surface npz (v,n)> <out npz> ; env LIFT=0.3
import sys, os, numpy as np
from scipy.spatial import cKDTree
D = np.load(sys.argv[1]); RF = np.load(sys.argv[2]); OU = np.load(sys.argv[3]); OUT = sys.argv[4]; LIFT = float(os.environ.get("LIFT", "0.3"))
RV, RN, OV, ON = RF["v"], RF["n"], OU["v"], OU["n"]
RN = RN * np.where(RN[:, 2:3] < 0, -1, 1); ON = ON * np.where(ON[:, 2:3] < 0, -1, 1)   # (upwards: these decorations sit on top)
V = D["v"]; i = cKDTree(RV).query(V)[1]; h = np.einsum("ij,ij->i", V - RV[i], RN[i]); tang = (V - RV[i]) - RN[i] * h[:, None]
j = cKDTree(OV).query(RV[i])[1]; V2 = OV[j] + ON[j] * (np.maximum(h, 0) + LIFT)[:, None] + tang
np.savez(OUT, v=V2, f=D["f"], tri_uv=D["tri_uv"])
print("DECOR pe suprafata: %d varfuri; inaltime %.1f..%.1f m; mutat fata de referinta medie %.1f, max %.1f m" % (
    len(V), h.min(), h.max(), np.linalg.norm(V2 - V, axis=1).mean(), np.linalg.norm(V2 - V, axis=1).max()))
