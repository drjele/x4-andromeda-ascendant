# Guides along the ribs' tips (asked: put guides on the ribs' tips too): through every vertebra's points, front to back -
# the edge lines (top and bottom, where the flat face turns into the curved edge) and the inner ends (top and bottom, in
# the body); lines already in the npz kept. Usage: python ureche_linii_varfuri.py <vertebre npz> <out.npz>
import sys, numpy as np
G = dict(np.load(sys.argv[1])); ks = sorted((k for k in G if k.startswith("vertebra")), key=lambda k: -G[k][0, 1])
L = {"linie_muchie_sus_D": [], "linie_muchie_jos_D": [], "linie_capat_sus_D": [], "linie_capat_jos_D": []}
for k in ks:
    A = G[k]; zt, zb = A[:, 2].max(), A[:, 2].min(); T = A[np.abs(A[:, 2] - zt) < 1e-3]; B = A[np.abs(A[:, 2] - zb) < 1e-3]
    L["linie_muchie_sus_D"].append(T[np.argmax(T[:, 0])]); L["linie_muchie_jos_D"].append(B[np.argmax(B[:, 0])])
    L["linie_capat_sus_D"].append(T[np.argmin(T[:, 0])]); L["linie_capat_jos_D"].append(B[np.argmin(B[:, 0])])
for k, v in L.items():
    if k in G: continue                                                # already made (edge lines from the margin)
    v = np.array(v); G[k] = v; print("%-20s y %.0f..%.0f, x %.0f..%.0f, z %.1f" % (k, v[:, 1].min(), v[:, 1].max(), v[:, 0].min(), v[:, 0].max(), v[0, 2]))
np.savez(sys.argv[2], **G)
