# A few clean guide lines on the edges of a body piece (asked for 169_C, like the rails of the red nacelles): from the
# piece's vertices, per 2 m slice along y, on each side: the outer edge (farthest from the middle), the top edge (outermost
# point still on the flat top: within TOLZ of the slice's top), the bottom edge (same, underneath) and, behind the U, the
# arms' inner edge (nearest to the middle); each row smoothed along y (gaussian, outliers dropped) into one smooth line,
# mirrored onto the other side exactly. Drawn as poly curves in collection GHIDAJE_<NAME>.
# Usage: blender -b <file.blend> --python ghid_169.py -- <object> <out.blend> [y_end]
import bpy, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OBJ, OUT = a[0], a[1]; YE = float(a[2]) if len(a) > 2 else -350.0
TOLZ, SG = float(os.environ.get("GHID_TOLZ", "1.0")), float(os.environ.get("GHID_NET", "4"))
o = bpy.data.objects[OBJ]; M = np.array(o.matrix_world); v = np.zeros(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", v); P = v.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
c0 = (P[:, 0].min() + P[:, 0].max()) / 2; P = P[P[:, 0] >= c0]; X = P[:, 0] - c0      # one side (+x), mirrored later
ytop = P[:, 1].max(); bins = np.arange(YE, ytop, 2.0); rows = {k: [] for k in ("exterior", "sus", "jos", "interior")}
for y0 in bins:
    m = np.abs(P[:, 1] - y0) <= 1.0
    if m.sum() < 6: continue
    q, x = P[m], X[m]; ed = x > x.max() - 0.5                           # outer edge: on a near-vertical side the single farthest
    rows["exterior"].append((x.max(), y0, float(np.mean(q[ed, 2]))))     # point hops up and down - take the side's middle
    t = q[:, 2] > q[:, 2].max() - TOLZ; j = np.argmax(np.where(t, x, -1)); rows["sus"].append((x[j], y0, q[j, 2]))
    b = q[:, 2] < q[:, 2].min() + TOLZ; j = np.argmax(np.where(b, x, -1)); rows["jos"].append((x[j], y0, q[j, 2]))
    if x.min() > 3.0: ei = x < x.min() + 0.5; rows["interior"].append((x.min(), y0, float(np.mean(q[ei, 2]))))
def clean(R):
    R = np.array(R)
    if len(R) < 8: return None
    n = int(3 * SG); k = np.exp(-0.5 * (np.arange(-n, n + 1) / SG) ** 2); k /= k.sum()
    for _ in range(2):                                                  # drop outliers against a smooth version, then smooth
        S_ = np.stack([np.convolve(np.pad(R[:, i], n, mode="edge"), k, "valid") for i in (0, 2)], 1)
        dev = np.linalg.norm(R[:, [0, 2]] - S_, axis=1); R = R[dev < max(4 * np.median(dev), 6.0)]   # only real spikes go
    S_ = np.stack([np.convolve(np.pad(R[:, i], n, mode="edge"), k, "valid") for i in (0, 2)], 1)
    return np.stack([S_[:, 0], R[:, 1], S_[:, 1]], 1)
CN = "GHIDAJE_" + OBJ.replace("expl_", "").replace("piesa_comp_", "")
col = bpy.data.collections.get(CN) or bpy.data.collections.new(CN)
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for ob in list(col.objects): bpy.data.objects.remove(ob)
mg = bpy.data.materials.get("ghidaj") or bpy.data.materials.new("ghidaj"); mg.diffuse_color = (1.0, 0.85, 0.0, 1)
for key, R in rows.items():
    L = clean(R)
    if L is None: continue
    for side, sg in (("D", 1), ("S", -1)):
        cu = bpy.data.curves.new(key, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.0; sp = cu.splines.new("POLY"); sp.points.add(len(L) - 1)
        for p, q in zip(sp.points, L): p.co = (c0 + sg * q[0], q[1], q[2], 1)
        cu.materials.append(mg); ob = bpy.data.objects.new("ghid_169_%s_%s" % (key, side), cu); col.objects.link(ob)
    print("LINIE %-9s %d puncte, y %.0f..%.0f" % (key, len(L), L[:, 1].min(), L[:, 1].max()))
UL = os.environ.get("GHID_U")                                           # the arms' inner edges as ONE U line (the shape's own U: arc
if UL:                                                                  # between the arms + the two tangent straight lines), height
    XE2, YE2, RU2, YA = [float(v) for v in UL.split(",")]; cy2 = YA - RU2   # taken from the piece (middle of its inner wall)
    Pp, Cc = np.array([XE2, YE2]), np.array([0.0, cy2]); d_ = np.linalg.norm(Cc - Pp); be = np.arcsin(RU2 / d_); u0 = (Cc - Pp) / d_
    tx2, ty2 = max([Pp + np.array([[np.cos(b), -np.sin(b)], [np.sin(b), np.cos(b)]]) @ u0 * np.sqrt(d_ ** 2 - RU2 ** 2) for b in (be, -be)], key=lambda p: p[0])
    a0 = np.arctan2(ty2 - cy2, tx2); line = [(XE2 + (tx2 - XE2) * t, YE2 + (ty2 - YE2) * t) for t in np.linspace(0, 1, 120)]
    arc = [(RU2 * np.cos(t), cy2 + RU2 * np.sin(t)) for t in np.linspace(a0, np.pi / 2, 30)[1:]]
    half = np.array(line + arc); U2 = np.vstack([half * [-1, 1], half[::-1][1:]])   # S line -> arc -> D line
    PA = v.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]; zs = []
    for x, y in U2:
        d = np.hypot(PA[:, 0] - c0 - x, PA[:, 1] - y); m = d < 2.5; zs.append(float(np.mean(PA[m, 2])) if m.any() else np.nan)
    zs = np.array(zs); g = ~np.isnan(zs); zs = np.interp(np.arange(len(zs)), np.nonzero(g)[0], zs[g])
    n = 6; kk = np.exp(-0.5 * (np.arange(-3 * n, 3 * n + 1) / n) ** 2); kk /= kk.sum(); zs = np.convolve(np.pad(zs, 3 * n, mode="edge"), kk, "valid")
    for ob in [ob for ob in col.objects if "interior" in ob.name]: bpy.data.objects.remove(ob)
    cu = bpy.data.curves.new("u", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.0; sp = cu.splines.new("POLY"); sp.points.add(len(U2) - 1)
    for p, (x, y), z in zip(sp.points, U2, zs): p.co = (c0 + x, y, z, 1)
    cu.materials.append(mg); col.objects.link(bpy.data.objects.new("ghid_169_interior_U", cu)); print("LINIE U interior: arc R %.0f la y %.0f, drepte pana la (+-%.0f, %.0f)" % (RU2, YA, XE2, YE2))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
