# The nacelle's ribs re-cut with a uniform angle to the blue guide (the V's point line), so neighbouring ribs meet flat
# instead of overlapping like fish scales. The current row (copied ribs, aligned, and the generated copies between them)
# gives the slots: every rib face's point corner projected onto the blue guide -> a parameter; consecutive parameters are
# one rib's slot, so the slots tile the guide without gaps. At each slot boundary s a cutting plane through the blue guide
# point: normal = the guide's tangent (set "perpendicular"), or that normal turned by a constant ANGLE about a constant
# local axis (set "inclinat": the average tilt axis of the copied ribs, in the guide's moving frame). The plane's 3 corners
# = the blue point and the two points where the plane cuts the green and the yellow guides. Every rib (copied or
# generated) is the same rib shape as now (its source copied rib's curved V, trilinear frame) rebuilt between its two
# plane sections. Copied = dark red, generated = light red. Each set in its own collection, beside the reference (DX, DY).
# The guides are evaluated a little past their ends (same cubic) so planes near the ends still cut all three.
# Usage: blender -b <completed.blend> --python rib_planes.py -- <aligned_corners.json> <guides.json> <out.blend> <dx>
#        <set_name> <angle_deg> <dy>  [<set_name> <angle_deg> <dy> ...]
import bpy, sys, json, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; CJ, GJ, OUT, DX = a[0], a[1], a[2], float(a[3]); SETS = [(a[i], float(a[i + 1]), float(a[i + 2])) for i in range(4, len(a), 3)]
R = json.load(open(CJ)); Gd = json.load(open(GJ)); sc = bpy.context.scene; N = len(R)
def bez(c, t): c = np.array(c); t = np.atleast_1d(t)[:, None]; return (1 - t) ** 3 * c[0] + 3 * (1 - t) ** 2 * t * c[1] + 3 * (1 - t) * t ** 2 * c[2] + t ** 3 * c[3]
TS = np.linspace(-0.05, 1.2, 50001); GU = [bez(r["control"], TS) for r in Gd["rails"]]               # 0 end1 (green), 1 point (blue), 2 end2 (yellow)
TB = np.gradient(GU[1], axis=0); TB /= np.linalg.norm(TB, axis=1)[:, None]
def face(k, f): c = np.array(R[k][f]); return np.array([c[1], c[0], c[2]])     # (point, end1, end2)
def frame(k):
    fb, ff = face(k, "spate"), face(k, "fata"); p, e1, e2 = (fb + ff) / 2; u, v = e1 - p, e2 - p; n = np.cross(u, v); n /= np.linalg.norm(n)
    hb, hf = np.dot(fb[0] - p, n), np.dot(ff[0] - p, n)
    if hf < hb: n, hb, hf = -n, -hb, -hf
    return p, u, v, n, hb, hf
def rib(k):
    o = bpy.data.objects["nervura_copiata_%02d_S" % k]; return np.array([o.matrix_world @ v.co for v in o.data.vertices]) - [DX, 0, 0], [tuple(p.vertices) for p in o.data.polygons]
def coords(k, P):
    # a, b along the rib's arms; t across its width, re-normalised piece by piece along the V (position s = a - b, binned):
    # the bar is curved and slightly twisted between its corners, so at every place along it its own width is mapped onto
    # [0, 1] - no part of the rib reaches past its two cutting planes into the neighbour (no tile overlap, top or bottom)
    p, u, v, n, hb, hf = frame(k); ab = np.linalg.solve(np.stack([u, v, n], 1), (P - p).T).T; A_, B_ = ab[:, 0], ab[:, 1]
    t = (ab[:, 2] - hb) / (hf - hb); pos = A_ - B_; edges = np.linspace(pos.min(), pos.max(), 25); b = np.clip(np.digitize(pos, edges) - 1, 0, 23)
    cen = 0.5 * (edges[:-1] + edges[1:]); lo = np.array([t[b == i].min() if (b == i).any() else np.nan for i in range(24)]); hi = np.array([t[b == i].max() if (b == i).any() else np.nan for i in range(24)])
    ok = ~np.isnan(lo); lo_ = np.interp(pos, cen[ok], lo[ok]); hi_ = np.interp(pos, cen[ok], hi[ok])
    return A_, B_, np.clip((t - lo_) / np.maximum(hi_ - lo_, 1e-6), 0, 1)
def rebuild(A_, B_, t, F0, F1):
    s0 = F0[0] + A_[:, None] * (F0[1] - F0[0]) + B_[:, None] * (F0[2] - F0[0]); s1 = F1[0] + A_[:, None] * (F1[1] - F1[0]) + B_[:, None] * (F1[2] - F1[0])
    return s0 * (1 - t[:, None]) + s1 * t[:, None]
def tpar(p): return int(np.argmin(np.linalg.norm(GU[1] - p, axis=1)))       # index on the blue guide
# the row as it is: faces in order (point corner), with the source rib and colour of each slot
faces_pts, slots = [], []                                                   # slots: (src rib, dark?)
for k in range(N):
    fb, ff = face(k, "spate"), face(k, "fata")
    if not faces_pts: faces_pts.append(fb[0])
    faces_pts.append(ff[0]); slots.append((k, True))
    if k + 1 < N:
        F0, F1 = ff, face(k + 1, "spate"); width = np.linalg.norm(F1.mean(0) - F0.mean(0))
        rw = 0.5 * (np.linalg.norm(ff.mean(0) - fb.mean(0)) + np.linalg.norm(face(k + 1, "fata").mean(0) - F1.mean(0))); n = max(1, int(round(width / rw)))
        for j in range(n):
            f1 = (j + 1) / n; faces_pts.append((F0 * (1 - f1) + F1 * f1)[0]); slots.append((k if (j + 0.5) / n < 0.5 else k + 1, False))
idx = np.array([tpar(p) for p in faces_pts])
order_ok = np.all(np.diff(idx) > 0) or np.all(np.diff(idx) < 0)
# the copied ribs' average tilt (for the "inclinat" set): their plane normal in the blue guide's moving frame (T, U, V)
Uf = np.cross(TB, [0, 0, 1.0]); Uf /= np.linalg.norm(Uf, axis=1)[:, None]; Vf = np.cross(TB, Uf)
tilts = []
for k in range(N):
    p, u, v, n, hb, hf = frame(k); i = tpar(p)
    if np.dot(n, TB[i]) < 0: n = -n
    tilts.append([np.dot(n, TB[i]), np.dot(n, Uf[i]), np.dot(n, Vf[i])])
axis_loc = np.cross([1, 0, 0], np.mean(tilts, 0)); axis_loc /= np.linalg.norm(axis_loc)   # the axis the copied ribs lean about (local)
def plane_corners(i, ang):
    T, U, V = TB[i], Uf[i], Vf[i]; ax = axis_loc[0] * T + axis_loc[1] * U + axis_loc[2] * V; ax /= np.linalg.norm(ax)
    th = np.radians(ang); n = T * np.cos(th) + np.cross(ax, T) * np.sin(th) + ax * np.dot(ax, T) * (1 - np.cos(th))   # Rodrigues
    p = GU[1][i]; out = [p]
    for g in (GU[0], GU[2]):                                                # the plane cut on the green and the yellow guide
        d = (g - p) @ n; j0 = int(np.argmin(np.linalg.norm(g - p, axis=1))); lo, hi = max(j0 - 8000, 0), min(j0 + 8000, len(g) - 1)
        s = np.sign(d[lo:hi]); ch = np.where(np.diff(s) != 0)[0]
        if len(ch) == 0: out.append(g[j0]); continue
        jj = lo + ch[np.argmin(np.abs(lo + ch - j0))]; w = d[jj] / (d[jj] - d[jj + 1]); out.append(g[jj] * (1 - w) + g[jj + 1] * w)
    return np.array([out[0], out[1], out[2]])                               # (point, end1, end2)
def mat(n_, c):
    m = bpy.data.materials.get(n_) or bpy.data.materials.new(n_); m.diffuse_color = c; m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = c; return m
dark, light = mat("nervura_copiata_set", (0.35, 0.03, 0.04, 1)), mat("nervura_noua_rosu_deschis", (0.85, 0.12, 0.10, 1))
src_cache = {}
for name, ang, dy in SETS:
    col = bpy.data.collections.new("SET_" + name); sc.collection.children.link(col)
    planes = [plane_corners(i, ang) for i in idx]
    for s_, ((src, is_dark), F0, F1) in enumerate(zip(slots, planes[:-1], planes[1:])):
        if src not in src_cache: P, F = rib(src); src_cache[src] = (coords(src, P), F)
        (A_, B_, t), F = src_cache[src]; V = rebuild(A_, B_, t, F0, F1)
        for side in (1, -1):
            W = V.copy(); W[:, 0] *= side; FF = F if side > 0 else [f[::-1] for f in F]
            me = bpy.data.meshes.new("n"); me.from_pydata((W + [DX, dy, 0]).tolist(), [], FF); me.materials.append(dark if is_dark else light)
            for p_ in me.polygons: p_.use_smooth = True
            ob = bpy.data.objects.new("%s_%03d%s" % (name, s_, "_S" if side > 0 else "_D"), me); col.objects.link(ob)
    # check: the angle of every cut plane to the blue guide's perpendicular, and the corners' distance to the guides
    angs = []
    for i, pc in zip(idx, planes):
        n = np.cross(pc[1] - pc[0], pc[2] - pc[0]); n /= np.linalg.norm(n); angs.append(np.degrees(np.arccos(min(1, abs(np.dot(n, TB[i]))))))
    bad = [k_ for k_, x in enumerate(angs) if abs(x - ang) > 1.0]; print("   felii cu unghi abatut >1 grad:", bad[:20], len(bad))
    print("SET %-12s unghi fata de perpendiculara pe linia albastra: %s grade (min %.1f max %.1f); %d nervuri pe parte" % (name, "%.0f" % ang, min(angs), max(angs), len(slots)))
t_ = bpy.data.curves.new("t", "FONT")
for name, ang, dy in SETS:
    tc = bpy.data.curves.new(name, "FONT"); tc.body = "%s (%g grade)" % (name, ang); to = bpy.data.objects.new("eticheta_" + name, tc); sc.collection.objects.link(to)
    to.location = (DX - 700, 600 + dy, 0); to.scale = (30, 30, 30)
print("ORDINE pe linia albastra %s, %d felii" % ("ok" if order_ok else "NU e monotona", len(idx) - 1))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
