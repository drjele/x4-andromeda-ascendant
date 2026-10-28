# PS rebuilt from the confirmed guides of the original (ref_teren.py): inside the smoothed plan outline, between the top and
# the bottom faces; the sides closed (asked: option 1 - where the original leaves them open behind the nose, a rounded side
# continuing the nose's edge): smooth maximum of the outline's distance and the two faces' distances, edges rounded RK m.
# Field on a 1 m grid (faces carried over from the guides' grid), surface at 0 (marching cubes). Ship coordinates, centred.
# Usage: python ps_din_ghidaje.py <teren.npz> <out.npz> [rk] [sheet.png ref.npz xc]
import sys, numpy as np, cv2
from scipy.ndimage import distance_transform_edt as edt, map_coordinates, gaussian_filter
from skimage.measure import marching_cubes
T = np.load(sys.argv[1]); OUT = sys.argv[2]; RK = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0; C = float(__import__("os").environ.get("PS_CELULA", "1"))   # grid step (0.5 keeps the exact faces' detail)
top, bot, x0, y0, CG = T["top"], T["bot"], float(T["x0"]), float(T["y0"]), float(T["cell"]); ol = T["outline"][:, :2]
if "foot" in T and __import__("os").environ.get("PS_PRELUNGIRE"):    # (off: its hard 3 m cut left beads; margine_rotunda.py does the
                                                                        # edge now) the faces carried smoothly past the footprint's edge (a
    ft = T["foot"].astype(bool); din = edt(ft) * CG > 2.0; wq = gaussian_filter(din.astype(float), 2.0 / CG)   # weighted mean from
    def ext_(F):                                                        # inside, not the nearest cell, which copied the raster's
        E = gaussian_filter(np.where(din, F, 0.0), 2.0 / CG) / np.maximum(wq, 1e-6)   # steps into the outline's band)
        _, (pi, pj) = edt(wq < 0.02, return_indices=True); E = np.where(wq < 0.02, E[pi, pj], E)
        return np.where(edt(ft) * CG > 3.0, F, E)
    top, bot = ext_(top.astype(float)), ext_(bot.astype(float))
X0, Y0 = ol[:, 0].min() - 15, ol[:, 1].min() - 15; NX, NY = int((np.ptp(ol[:, 0]) + 30) / C), int((np.ptp(ol[:, 1]) + 30) / C)
S = 4; m = np.zeros((NY * S, NX * S), np.uint8); cv2.fillPoly(m, [np.round((ol - [X0, Y0]) / C * S).astype(np.int32)], 1)   # outline, fine
d2 = ((edt(m == 0) - edt(m == 1)) * C / S)[S // 2::S, S // 2::S][:NY, :NX].astype(np.float32)          # its distance (< 0 inside)
xs = X0 + (np.arange(NX) + 0.5) * C; ys = Y0 + (np.arange(NY) + 0.5) * C; X, Y = np.meshgrid(xs, ys, indexing="xy")
g = lambda F: map_coordinates(F, [(Y - y0) / CG - 0.5, (X - x0) / CG - 0.5], order=1, mode="nearest").astype(np.float32)
zt, zb = g(top), g(bot)
gty, gtx = np.gradient(zt, C); gby, gbx = np.gradient(zb, C); st, sb = np.sqrt(1 + gtx ** 2 + gty ** 2), np.sqrt(1 + gbx ** 2 + gby ** 2)
zs = np.arange(np.floor(zb.min()) - 6, np.ceil(zt.max()) + 6, C); F = np.empty((len(zs), NY, NX), np.float32)
sm = lambda a, b, k: (a + b + np.sqrt((a - b) ** 2 + k ** 2)) / 2
RO = float(__import__("os").environ.get("PS_RK_CONTUR", "3"))          # the plan outline's edge rounded less (the lens edge at the nose
for k, z in enumerate(zs): F[k] = sm(d2, sm((z - zt) / st, (zb - z) / sb, RK), RO)   # keeps its width and length)
F = gaussian_filter(F, 0.7)
v, f, _, _ = marching_cubes(F, 0.0, spacing=(C, C, C)); v = v[:, [2, 1, 0]] + [xs[0], ys[0], zs[0]]; f = f[:, ::-1]
np.savez(OUT, v=v.astype(np.float32), f=f.astype(np.int32))
print("PS DIN GHIDAJE: x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f; muchii rotunjite %.0f m; %d varfuri, %d fete" % (
    v[:, 0].min(), v[:, 0].max(), v[:, 1].min(), v[:, 1].max(), v[:, 2].min(), v[:, 2].max(), RK, len(v), len(f)))
if len(sys.argv) > 6:                                                   # check sheet: the new piece's cuts (black) over the original's (grey)
    import trimesh, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    R = np.load(sys.argv[5]); rv = R["v"].astype(float).copy(); rv[:, 0] -= float(sys.argv[6]); tr = trimesh.Trimesh(rv, R["f"], process=False)
    tn = trimesh.Trimesh(v, f, process=False); YS = [440, 380, 300, 220, 140, 60, 0, -40]
    fig, ax = plt.subplots(len(YS) + 1, 1, figsize=(14, 2.7 * (len(YS) + 1)))
    for a, y in zip(ax, YS):
        for q in trimesh.intersections.mesh_plane(tr, [0, 1, 0], [0, y, 0]): a.plot(q[:, 0], q[:, 2], "-", color="0.65", lw=1)
        for q in trimesh.intersections.mesh_plane(tn, [0, 1, 0], [0, y, 0]): a.plot(q[:, 0], q[:, 2], "k-", lw=1.2)
        a.set_title("y = %d: original (gri), piesa noua (negru)" % y, fontsize=9); a.set_aspect("equal"); a.grid(alpha=.3)
    a = ax[-1]
    for x, c in ((0, "k"), (60, "b"), (120, "g")):
        for q in trimesh.intersections.mesh_plane(tr, [1, 0, 0], [x, 0, 0]): a.plot(q[:, 1], q[:, 2], "-", color="0.7", lw=.8)
        for q in trimesh.intersections.mesh_plane(tn, [1, 0, 0], [x, 0, 0]): a.plot(q[:, 1], q[:, 2], "-", color=c, lw=1.1)
    a.set_title("profile lungi x = 0 (negru), 60 (albastru), 120 (verde); original gri", fontsize=9); a.set_aspect("equal"); a.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(sys.argv[4], dpi=95); print("PLANSA", sys.argv[4])
