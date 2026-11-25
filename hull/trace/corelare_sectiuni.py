# Sections of the aligned models overlaid (hull object only, no decorations): left half of each picture = the models' S half,
# right half = the same S half mirrored, plus the confirmed ship in grey; planes y = const, then x = const and z = const.
# Usage: python corelare_sectiuni.py <dir with npz> <out_prefix>
import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
D, OUT = sys.argv[1:3]
def load(f, hull=None):
    d = np.load(f"{D}/{f}.npz"); t = d["t"]; n = list(d["n"])
    if hull: t = t[np.isin(d["o"], [n.index(h) for h in hull])]
    return d["v"][t]
def sec(T, ax, c):
    s = T[:, :, ax] - c; k = (s.min(1) < 0) & (s.max(1) > 0); T, s = T[k], s[k]; out = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        f = (s[:, i] < 0) != (s[:, j] < 0); w = np.where(f, s[:, i] / np.where(f, s[:, i] - s[:, j], 1), 0)[:, None]; p = T[:, i] + (T[:, j] - T[:, i]) * w; p[~f] = np.nan; out.append(p)
    P = np.stack(out, 1); r = []
    for q in P:
        g = q[~np.isnan(q[:, 0])]
        if len(g) == 2: r.append(g)
    return np.array(r).reshape(-1, 2, 3)
M = [("nava noua (confirmata)", load("ASAMBLAT_NOU"), "0.72", .7), ("grannyte (NAVA REPO)", load("NAVA_REPO_XMF_al"), "#2a9d3a", .9),
     ("Binkley 084 (REFERINTA, S)", load("REFERINTA", ["R001 084_D", "R005 146_C"]), "#d62828", 1.3), ("morenostefanuto Cube (S)", load("moreno_v17_al", ["Cube", "NurbsPath.038_Mesh.027"]), "#1d4ed8", 1.3)]
def draw(planes, ax, h, w, lim, fn, cols, size):
    f, A = plt.subplots(-(-len(planes) // cols), cols, figsize=size); A = np.atleast_1d(A).ravel()
    for a, c in zip(A, planes):
        for n, T, col, lw in M:
            L = sec(T, ax, c)
            if len(L) and ax != 0: L = L[(L[:, :, 0] < 5).all(1)]; L = np.vstack([L, L * [-1, 1, 1]])
            a.add_collection(LineCollection(L[:, :, [h, w]], colors=col, linewidths=lw, label=n))
        a.set_xlim(*lim[0]); a.set_ylim(*lim[1]); a.set_aspect("equal"); a.grid(alpha=.25); a.set_title(f"{'xyz'[ax]} = {c}", fontsize=10)
    for a in A[len(planes):]: a.axis("off")
    A[0].legend(fontsize=7, loc="upper right"); plt.tight_layout(); plt.savefig(OUT + fn, dpi=75); plt.close()
draw([1100, 950, 800, 600, 400, 250, 100, 0, -50, -100, -150, -200, -275, -350, -425, -500, -600, -700], 1, 0, 2, ((-720, 720), (-390, 360)), "_y.png", 3, (24, 30))
draw([0, -60, -120, -200, -280, -360, -440, -520, -600, -650], 0, 1, 2, ((-900, 1400), (-390, 360)), "_x.png", 2, (24, 24))
draw([140, 100, 50, 0, -50, -100, -150, -200, -250, -300], 2, 1, 0, ((-900, 1400), (-720, 20)), "_z.png", 2, (24, 24))
