# The red attack wings on the inner edge of each front arc, from the root over the body to about half way:
# a V-section blade that follows the arc exactly, both faces ribbed with rounded piano keys across the strip,
# framed by round metal rails along its apex and base edges.
import bpy, bmesh, json, math, sys
import numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
sys.path.insert(0, f"{D}/arms"); from a_frame import member, frame, cast
P = json.load(open(f"{D}/arms/a_params.json")); N = json.load(open(f"{D}/arms/a_deco.json"))["wing"]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in ("arc_wing_r", "arc_wing_l")]: bpy.data.objects.remove(o)
b = bmesh.new(); b.from_mesh(sc.objects["arm_r"].data); T = BVHTree.FromBMesh(b)
C, f, W, H, R = member(P["members"]["arm"], 60)
idx = np.where((f >= N["f"][0]) & (f <= N["f"][1]))[0]
s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C[idx], axis=0), axis=1))]
kk = np.clip((0.5 + 0.5 * np.cos(2 * np.pi * s / N["keys"]["pitch"])) * 1.5 - 0.25, 0, 1); key = kk * kk * (3 - 2 * kk) * N["keys"]["h"]
reach = np.interp(f[idx], *zip(*N["reach"])); base = np.interp(f[idx], *zip(*N["base"]))
a0, tilt, m = math.radians(N["angle"]), math.radians(N["tilt"]), 6
bm = bmesh.new(); rows = []; rails = [[], [], []]
for n, k in enumerate(idx):
    t, w, u = frame(C, k, oriented=True); d = w * math.cos(a0) + u * math.sin(a0)
    hit, nrm = cast(T, C[k], d); up = u - t * u.dot(t); up /= np.linalg.norm(up)
    if hit is None: continue                                            # the path runs inside the plate here
    bl = nrm * math.cos(tilt) + up * math.sin(tilt); apex = hit + bl * reach[n]
    tb, tn = cast(T, C[k], hit + up * base[n] / 2 - C[k]); bb, bn = cast(T, C[k], hit - up * base[n] / 2 - C[k])
    if tb is None or bb is None or max(np.linalg.norm(tb - hit), np.linalg.norm(bb - hit)) > 1.5 * base[n] + 4: continue   # a cast that escaped the edge
    tb, bb = tb - tn * 2, bb - bn * 2                                   # the base sits inside the arm, so the blade grows out of it
    row = []
    for side, bp in ((1, tb), (-1, bb)):
        fn = np.cross(apex - bp, t) * side; fn /= np.linalg.norm(fn); fn = fn if fn.dot(up) * side > 0 else -fn
        pts = [bp + (apex - bp) * q + fn * key[n] * math.sin(math.pi * q) for q in np.linspace(0, 1, m + 1)]
        row.append([bm.verts.new(p) for p in (pts if side > 0 else pts[:-1])])
    rows.append((row[0], row[1])); rails[0].append(apex); rails[1].append(tb + tn * 1.5); rails[2].append(bb + bn * 1.5)
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
# the metal frame: round rails along the apex and along both base edges, tapering to nothing at the ends
for o in [o for o in sc.objects if o.name in ("arc_wing_frame_r", "arc_wing_frame_l")]: bpy.data.objects.remove(o)
bf = bmesh.new(); K = 10
for rail in rails:
    rings = []
    for n, p in enumerate(rail):
        q = n / (len(rail) - 1); r = N["frame"] * min(1.0, 6 * q, 6 * (1 - q)) ** 0.5 + 0.2
        t = rail[min(n + 1, len(rail) - 1)] - rail[max(n - 1, 0)]; t /= np.linalg.norm(t); a = np.cross(t, [0, 0, 1.0]); a /= np.linalg.norm(a); b = np.cross(t, a)
        rings.append([bf.verts.new(p + (a * math.cos(w) + b * math.sin(w)) * r) for w in np.linspace(0, 2 * math.pi, K, endpoint=False)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(K): bf.faces.new((r0[k], r0[(k + 1) % K], r1[(k + 1) % K], r1[k]))
    bf.faces.new(rings[0][::-1]); bf.faces.new(rings[-1])
bmesh.ops.recalc_face_normals(bf, faces=bf.faces[:])
mf = bpy.data.meshes.new("arc_wing_frame_r"); bf.to_mesh(mf)
for p in mf.polygons: p.use_smooth = True
sc.collection.objects.link(bpy.data.objects.new("arc_wing_frame_r", mf))
mfl = mf.copy(); mfl.name = "arc_wing_frame_l"; mfl.transform(Matrix.Scale(-1, 4, (1, 0, 0))); mfl.flip_normals()
sc.collection.objects.link(bpy.data.objects.new("arc_wing_frame_l", mfl))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("WING ok", len(me.polygons))
