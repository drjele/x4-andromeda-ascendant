# nt_146 new vs reference: plan, long profile, cuts. Usage: python g146_cmp.py <piece dir> <out.png>
import numpy as np, trimesh, sys, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
Z = np.load(sys.argv[1] + "/146.npz"); R = np.load(sys.argv[1] + "/146_ref_S.npz"); m = trimesh.Trimesh(Z["v"], Z["f"], process=False); r = trimesh.Trimesh(R["v"] * [-1, 1, 1], R["f"], process=False)
YS = [430, 300, 150, 40, -20, -50, -75, -95, -115, -200, -450, -700]; fig, ax = plt.subplots(3, 5, figsize=(22, 10)); ax = ax.ravel()
for a, y in zip(ax, YS):
    for q in trimesh.intersections.mesh_plane(r, [0, 1, 0], [0, y, 0]): a.plot(q[:, 0], q[:, 2], color=".6", lw=1.6)
    for q in trimesh.intersections.mesh_plane(m, [0, 1, 0], [0, y, 0]): a.plot(q[:, 0], q[:, 2], "r", lw=.6)
    a.set_title("y=%d" % y, fontsize=8); a.set_aspect("equal"); a.set_xlim(left=-3); a.grid(alpha=.3)
a = ax[12]; a.plot(*m.vertices[:, :2].T, "r,"); a.plot(*r.vertices[:, :2].T, "k,"); a.set_aspect("equal"); a.set_xlim(0, 520)
a = ax[13]
for x in (0, 100):
    for q in trimesh.intersections.mesh_plane(r, [1, 0, 0], [x, 0, 0]): a.plot(q[:, 1], q[:, 2], color=".6", lw=1.4)
    for q in trimesh.intersections.mesh_plane(m, [1, 0, 0], [x, 0, 0]): a.plot(q[:, 1], q[:, 2], "r", lw=.6)
a.set_aspect("equal"); a.grid(alpha=.3); a.set_title("x=0,100")
fig.tight_layout(); fig.savefig(sys.argv[2], dpi=75)
