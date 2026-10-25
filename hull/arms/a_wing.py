# The red attack wings on the inner edge of each front arc, from the V-plate junction to about half way: a V
# section swept along the arc in the arc's own frame (one continuous base line on the strap's inner side, one
# continuous apex line in the strap's plane), widest at the junction and tapering along the arc; the piano
# keys are a displacement of the two faces only, fading to nothing at the base and the apex.
import bpy, bmesh, json, math, sys
import numpy as np
from mathutils import Matrix
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
sys.path.insert(0, f"{D}/arms"); from a_frame import member, frame
P = json.load(open(f"{D}/arms/a_params.json")); N = json.load(open(f"{D}/arms/a_deco.json"))["wing"]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in ("arc_wing_r", "arc_wing_l")]: bpy.data.objects.remove(o)
C, f, W, H, R = member(P["members"]["arm"], 10)
s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]; t = np.r_[np.arange(0, s[-1], N.get("step", 4.0)), s[-1]]
Cu = np.stack([np.interp(t, s, C[:, c]) for c in range(3)], 1); fu, Wu, Hu, Ru = (np.interp(t, s, v) for v in (f, W, H, R))
idx = np.where((fu >= N["f"][0]) & (fu <= N["f"][1]))[0]; su = t[idx] - t[idx[0]]
reach = np.interp(fu[idx], *zip(*N["reach"]))
lift = np.interp(fu[idx], *zip(*N["lift"])) if "lift" in N else np.zeros(len(idx))   # the apex raised toward the V plate at the junction
kk = np.clip((0.5 + 0.5 * np.cos(2 * np.pi * su / N["keys"]["pitch"])) * 1.5 - 0.25, 0, 1); key = kk * kk * (3 - 2 * kk) * N["keys"]["h"]
m = 6; bm = bmesh.new(); rows = []
for n, k in enumerate(idx):
    tt, w, u = frame(Cu, k, oriented=True); half = Hu[k] / 2 - min(Ru[k] * Hu[k] / 2, Wu[k] / 2, Hu[k] / 2) * 0.35   # the flat inner side of the strap
    edge = Cu[k] - w * (Wu[k] / 2 - N["sink"]); apex = Cu[k] - w * (Wu[k] / 2 + reach[n]) + np.array([0, 0, lift[n]])
    tb, bb = edge + u * half * N["base_scale"], edge - u * half * N["base_scale"]
    row = []
    for side, bp in ((1, tb), (-1, bb)):
        fn = np.cross(apex - bp, tt) * side; fn /= np.linalg.norm(fn); fn = fn if fn.dot(u) * side > 0 else -fn
        pts = [bp + (apex - bp) * q + fn * key[n] * math.sin(math.pi * q) for q in np.linspace(0, 1, m + 1)]
        row.append([bm.verts.new(p) for p in (pts if side > 0 else pts[:-1])])
    rows.append((row[0], row[1]))
def loop(r): return r[0] + r[1][::-1]
for (t0, b0), (t1, b1) in zip(rows, rows[1:]):
    for q in range(m): bm.faces.new((t0[q], t0[q + 1], t1[q + 1], t1[q]))
    for q in range(m - 1): bm.faces.new((b0[q + 1], b0[q], b1[q], b1[q + 1]))
    bm.faces.new((b0[m - 1], t0[m], t1[m], b1[m - 1])); bm.faces.new((t0[0], b0[0], b1[0], t1[0]))
for r, rev in ((rows[0], True), (rows[-1], False)):
    l = loop(r); bm.faces.new(l[::-1] if rev else l)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("arc_wing_r"); bm.to_mesh(me)
for p in me.polygons: p.use_smooth = True
sc.collection.objects.link(bpy.data.objects.new("arc_wing_r", me))
ml = me.copy(); ml.name = "arc_wing_l"; ml.transform(Matrix.Scale(-1, 4, (1, 0, 0))); ml.flip_normals()
sc.collection.objects.link(bpy.data.objects.new("arc_wing_l", ml))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("WING ok", len(me.polygons))
