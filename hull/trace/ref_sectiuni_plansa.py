# Sheet of the reference piece cut by planes (to read its real shape before drawing guides): cross sections (x-z) at chosen
# y, the long profile (y-z) at chosen x, all exact (mesh / plane intersections), centred on the ship's middle (XC). One image.
# Usage: python ref_sectiuni_plansa.py <ref.npz (v,f)> <out.png> <xc> <y,y,...> <x,x,...> [title]
import sys, numpy as np, trimesh, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
Z = np.load(sys.argv[1]); OUT = sys.argv[2]; XC = float(sys.argv[3]); YS = [float(t) for t in sys.argv[4].split(",")]; XS = [float(t) for t in sys.argv[5].split(",")]
T = sys.argv[6] if len(sys.argv) > 6 else ""
v = Z["v"].copy(); v[:, 0] -= XC; tm = trimesh.Trimesh(v, Z["f"], process=False)
n = len(YS) + 1; fig, ax = plt.subplots(n, 1, figsize=(14, 3.2 * n))
for a, y in zip(ax, YS):
    for q in trimesh.intersections.mesh_plane(tm, [0, 1, 0], [0, y, 0]): a.plot(q[:, 0], q[:, 2], "k-", lw=1)   # raw segments
    a.set_title("sectiune y = %.0f (privit din fata)" % y, fontsize=9); a.set_aspect("equal"); a.grid(alpha=.3); a.axvline(0, color="r", lw=.5)
a = ax[-1]
for x, c in zip(XS, ["k", "b", "g", "m"]):
    for q in trimesh.intersections.mesh_plane(tm, [1, 0, 0], [x, 0, 0]): a.plot(q[:, 1], q[:, 2], "-", color=c, lw=1)
    a.plot([], [], color=c, label="x = %.0f" % x)
a.legend(fontsize=8); a.set_title("profil lung (y spre dreapta = spre varf)", fontsize=9); a.set_aspect("equal"); a.grid(alpha=.3)
fig.suptitle(T); fig.tight_layout(); fig.savefig(OUT, dpi=110); print("PLANSA", OUT)
