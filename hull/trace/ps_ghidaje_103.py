# Guide lines for component 103+118 (asked: straight edges, the piece is in principle a V - drawn separately so the user
# confirms the surfaces before it is rebuilt): from the piece's section curves (ps_banda103.py: per y, inner/top end ->
# outer/bottom end) three point rows - the inner edge (first point), the V's fold (the point farthest from the chord) and
# the outer edge (last point) - each fitted by a straight 3-D line (least squares), cut at the piece's first and last
# section; the two ends closed by the V (inner -> fold -> outer). Drawn as poly curves (collection GHIDAJE_103_118) for _S
# and mirrored _D, with the two V faces as preview surfaces (ruled between the lines). Ship coordinates (x + DX).
# Usage: blender -b <file.blend> --python ps_ghidaje_103.py -- <banda103.npz> <out.blend> <dx>
import bpy, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; D = np.load(a[0]); OUT, DX = a[1], float(a[2])
C, ys = D["C"], D["ys"]; K, NU = C.shape[:2]
P3 = lambda i: np.stack([C[:, i, 0], ys, C[:, i, 1]], 1)
ch = C[:, -1] - C[:, 0]; ch_n = ch / np.linalg.norm(ch, axis=1)[:, None]
dist = np.abs((C[:, :, 0] - C[:, :1, 0]) * ch_n[:, None, 1] - (C[:, :, 1] - C[:, :1, 1]) * ch_n[:, None, 0])
kf = np.argmax(dist, axis=1); FOLD = np.stack([C[np.arange(K), kf, 0], ys, C[np.arange(K), kf, 1]], 1)
NSEG = int(os.environ.get("GHID_TRONSOANE", "2"))
def fit(Pts, yb):                                                       # straight pieces between the breaks, joined (continuous)
    knots = np.r_[ys[0], yb, ys[-1]]; Bm = np.stack([np.ones_like(Pts[:, 1])] + [np.clip(Pts[:, 1] - k, 0, None) for k in knots[:-1]], 1)[:, :len(knots)]
    cx = np.linalg.lstsq(Bm, Pts[:, 0], rcond=None)[0]; cz = np.linalg.lstsq(Bm, Pts[:, 2], rcond=None)[0]
    ev = lambda y: np.stack([np.ones_like(y)] + [np.clip(y - k, 0, None) for k in knots[:-1]], -1)[..., :len(knots)]
    L = lambda y: np.stack([ev(np.atleast_1d(y)) @ cx, np.atleast_1d(y), ev(np.atleast_1d(y)) @ cz], -1)[0] if np.ndim(y) == 0 else np.stack([ev(y) @ cx, y, ev(y) @ cz], -1)
    dev = np.linalg.norm(np.stack([Bm @ cx - Pts[:, 0], Bm @ cz - Pts[:, 2]], 1), axis=1); return L, dev
rows = [P3(0), FOLD, P3(NU - 1)]; best = None
for yb in (np.linspace(ys[0] + 60, ys[-1] - 60, 60) if NSEG == 2 else [None]):
    yb_ = [] if yb is None else [yb]
    devs = [fit(r, yb_)[1] for r in rows]; err = sum(np.median(d) for d in devs)
    if best is None or err < best[0]: best = (err, yb_)
YB_ = best[1]; (LI, dI), (LF, dF), (LO, dO) = [fit(r, YB_) for r in rows]
print("COTITURA la y %s" % (np.round(YB_, 0).tolist())); y0, y1 = ys[0], ys[-1]
CN = os.environ.get("GHID_COL", "GHIDAJE_103_118"); OFFS = {k: np.array([float(v) for v in os.environ.get("GHID_OFF_" + k, "0,0,0").split(",")]) for k in ("S", "D")}
col = bpy.data.collections.get(CN) or bpy.data.collections.new(CN)
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for o in list(col.objects):
    if o.name.startswith("ghid_103_"): bpy.data.objects.remove(o)
mg = bpy.data.materials.get("ghidaj") or bpy.data.materials.new("ghidaj"); mg.diffuse_color = (1.0, 0.85, 0.0, 1)
ms = bpy.data.materials.get("ghidaj_suprafata") or bpy.data.materials.new("ghidaj_suprafata"); ms.diffuse_color = (0.3, 0.7, 1.0, 0.5)
def curve(name, pts, sg):
    pts = [np.array(p) + OFFS["S" if sg > 0 else "D"] * [sg, 1, 1] for p in pts]
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.8; sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (sg * q[0] + DX, q[1], q[2], 1)
    o = bpy.data.objects.new(name, cu); cu.materials.append(mg); col.objects.link(o)
for side, sg in (("S", 1), ("D", -1)):
    yk = [y0] + YB_ + [y1]
    curve("ghid_103_margine_interioara_" + side, [LI(y) for y in yk], sg); curve("ghid_103_indoitura_V_" + side, [LF(y) for y in yk], sg)
    curve("ghid_103_margine_exterioara_" + side, [LO(y) for y in yk], sg)
    for yb_ in YB_: curve("ghid_103_cotitura_" + side, [LI(yb_), LF(yb_), LO(yb_)], sg)
    curve("ghid_103_capat_spate_" + side, [LI(y0), LF(y0), LO(y0)], sg); curve("ghid_103_capat_fata_" + side, [LI(y1), LF(y1), LO(y1)], sg)
    yy = np.unique(np.r_[np.linspace(y0, y1, 40), YB_]); V, F = [], []
    for A_, B_ in ((LI, LF), (LF, LO)):                                 # the two V faces, ruled between the lines
        b = len(V); V += [tuple((sg * p[0] + DX + OFFS[side][0], p[1] + OFFS[side][1], p[2] + OFFS[side][2])) for y in yy for p in (A_(y), B_(y))]
        F += [(b + 2 * i, b + 2 * i + 1, b + 2 * i + 3, b + 2 * i + 2) for i in range(len(yy) - 1)]
    me = bpy.data.meshes.new("ghid_103_suprafete_" + side); me.from_pydata(V, [], F); me.materials.append(ms)
    o = bpy.data.objects.new("ghid_103_suprafete_" + side, me); col.objects.link(o)
print("GHIDAJE 103: y %.0f..%.0f; abatere fata de piesa (max/mediana): margine interioara %.1f/%.1f m, indoitura %.1f/%.1f m, margine exterioara %.1f/%.1f m" % (y0, y1, dI.max(), np.median(dI), dF.max(), np.median(dF), dO.max(), np.median(dO)))
print("  capat spate: interior %s indoitura %s exterior %s" % (np.round(LI(y0)).tolist(), np.round(LF(y0)).tolist(), np.round(LO(y0)).tolist()))
print("  capat fata:  interior %s indoitura %s exterior %s" % (np.round(LI(y1)).tolist(), np.round(LF(y1)).tolist(), np.round(LO(y1)).tolist()))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
