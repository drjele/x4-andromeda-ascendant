# Step 2 of the nacelle: the 3 guide lines (rails) through the copied ribs' corners and their curvature, to check them.
# Per rib and rail the corner taken in the middle of the bar (mean of its back and front face corners); per rail a
# least-squares cubic Bezier through those points (4 control points: one smooth bend, the smallest deviation), the
# deviation of every corner from it reported. Drawn beside the untouched reference: the raw corner polyline (thin, grey),
# the fitted rail (thick, its colour), and a curvature comb (a short line at each sample across the rail, as long as the
# curvature there; an even comb = one even bend, a comb that changes side = an inflection).
# The three rails continued ahead of the first rib into one common point (EXT x the V's width ahead), without a kink.
# Usage: blender -b <step1.blend> --python rib_rails.py -- <corners.json> <out.blend> <rails.json> <dx> [ext]
import bpy, sys, json, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; CJ, OUT, RJ, DX = a[0], a[1], a[2], float(a[3]); EXT = float(a[4]) if len(a) > 4 else 2.0; R = json.load(open(CJ)); sc = bpy.context.scene
NAMES = ["capat1 (verde)", "varf (albastru)", "capat2 (galben)"]; COLS = [(0.1, 0.8, 0.2, 1), (0.1, 0.4, 1.0, 1), (1.0, 0.8, 0.1, 1)]
pts = np.array([[(np.array(r["spate"][i]) + np.array(r["fata"][i])) / 2 for i in range(3)] for r in R])     # (ribs, 3, xyz)
def bez(c, t): t = np.atleast_1d(t)[:, None]; return (1 - t) ** 3 * c[0] + 3 * (1 - t) ** 2 * t * c[1] + 3 * (1 - t) * t ** 2 * c[2] + t ** 3 * c[3]
def dbez(c, t, n):
    t = np.atleast_1d(t)[:, None]
    if n == 1: return 3 * ((1 - t) ** 2 * (c[1] - c[0]) + 2 * (1 - t) * t * (c[2] - c[1]) + t ** 2 * (c[3] - c[2]))
    return 6 * ((1 - t) * (c[2] - 2 * c[1] + c[0]) + t * (c[3] - 2 * c[2] + c[1]))
fits = []
for i in range(3):
    P = pts[:, i]; t = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; t /= t[-1]
    for _ in range(5):                                                      # least squares, then the parameters re-projected onto the curve
        Bm = np.stack([(1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3], 1); c = np.linalg.lstsq(Bm, P, rcond=None)[0]
        ts = np.linspace(0, 1, 2001); Q = bez(c, ts); t = ts[np.argmin(np.linalg.norm(P[:, None] - Q[None], axis=2), axis=1)]; t[0], t[-1] = 0, 1
    d = np.linalg.norm(bez(c, t) - P, axis=1); fits.append((c, t, d))
# the meeting point ahead of the first rib (t = 0 end): along the rails' mean direction there, as far ahead as the V is wide;
# each rail continued by a single-bend curve leaving with its own tangent (no kink, no inflection) into the point,
# where the three close sharply
d0 = -np.mean([dbez(f[0], 0.0, 1)[0] / np.linalg.norm(dbez(f[0], 0.0, 1)[0]) for f in fits], 0); d0 /= np.linalg.norm(d0)
p0s = np.array([bez(f[0], 0.0)[0] for f in fits]); width = max(np.linalg.norm(p0s[i] - p0s[j]) for i in range(3) for j in range(3))
apex = p0s.mean(0) + d0 * EXT * width; ext = []
for i, f in enumerate(fits):
    # a quadratic curve (one bend, never an inflection), leaving along the rail's own tangent; written as a cubic
    P0 = p0s[i]; T0 = -dbez(f[0], 0.0, 1)[0]; T0 /= np.linalg.norm(T0); Q1 = P0 + T0 * np.dot(apex - P0, T0) * 0.5
    ext.append(np.array([P0, P0 + 2 / 3 * (Q1 - P0), apex + 2 / 3 * (Q1 - apex), apex]))
json.dump({"apex": apex.tolist(), "rails": [{"rail": NAMES[i], "control": f[0].tolist(), "extension_control": ext[i].tolist(), "t": f[1].tolist(), "deviation_m": f[2].tolist()} for i, f in enumerate(fits)]}, open(RJ, "w"), indent=1)
col = bpy.data.collections.new("GHIDAJE"); sc.collection.children.link(col)
def mat(n, c): m = bpy.data.materials.new(n); m.diffuse_color = c; m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = c; return m
def curve(name, P, r, m, side):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; s_ = cu.splines.new("POLY"); s_.points.add(len(P) - 1)
    for k, p in enumerate(P): s_.points[k].co = (*(p * [side, 1, 1] + [DX, 0, 0]), 1)
    ob = bpy.data.objects.new(name, cu); cu.materials.append(m); col.objects.link(ob)
grey = mat("colturi_brut", (0.5, 0.5, 0.5, 1)); comb_m = mat("pieptene_curbura", (0.9, 0.2, 0.9, 1))
for o in [o for o in bpy.data.objects if o.name.startswith(("sina_", "varf_"))]: o.hide_set(True); o.hide_render = True
for side in (1, -1):
    sfx = "_S" if side > 0 else "_D"
    for i, (c, t, d) in enumerate(fits):
        curve("colturi_brut_%d%s" % (i + 1, sfx), pts[:, i], 0.5, grey, side)
        ts = np.linspace(0, 1, 200); full = np.vstack([bez(ext[i], np.linspace(1, 0, 60))[:-1], bez(c, ts)])
        curve("ghidaj_%d%s" % (i + 1, sfx), full, 1.5, mat("ghidaj_%d" % i, COLS[i]), side)
        for cc, rng in ((c, np.linspace(0, 1, 60)), (ext[i], np.linspace(0, 0.97, 18))):   # curvature comb (rail and its extension)
            for tt in rng:
                d1 = dbez(cc, tt, 1)[0]; d2 = dbez(cc, tt, 2)[0]; k = np.linalg.norm(np.cross(d1, d2)) / np.linalg.norm(d1) ** 3
                nvec = d2 - d1 * np.dot(d1, d2) / np.dot(d1, d1); nvec /= max(np.linalg.norm(nvec), 1e-9); p0 = bez(cc, tt)[0]
                curve("pieptene_%d_%04d%s" % (i + 1, int(tt * 999) + (0 if cc is c else 1000), sfx), np.array([p0, p0 - nvec * min(k, 0.02) * 6000]), 0.3, comb_m, side)
for i, (c, t, d) in enumerate(fits):
    print("GHIDAJ %-16s abatere colturi m: medie %.2f, max %.2f (nervura %d); lungime %.0f m" % (NAMES[i], d.mean(), d.max(), int(np.argmax(d)), np.sum(np.linalg.norm(np.diff(bez(c, np.linspace(0, 1, 400)), axis=0), axis=1))))
print("PUNCT DE INTALNIRE la %.0f m in fata primei nervuri (V lat de %.0f m acolo)" % (np.linalg.norm(apex - p0s.mean(0)), width))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
