# Fine rails along each arm: the double ribs on the outer flank behind the pod, a line over the aft loop
# and the paired lines along the upper member; thin tubes set half into the arm surface, tapering at both ends.
import bpy, bmesh, json, math, sys
import numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
sys.path.insert(0, f"{D}/arms"); from a_frame import member, frame, cast
A = json.load(open(f"{D}/arms/a_params.json"))["members"]["arm"]; R = json.load(open(f"{D}/arms/a_deco.json"))["ribs"]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in ("ribs_r", "ribs_l")]: bpy.data.objects.remove(o)
b = bmesh.new(); b.from_mesh(sc.objects["arm_r"].data); T = BVHTree.FromBMesh(b)
C, f, W, H, _ = member(A)
bm = bmesh.new(); K = 12
for rib in R:
    sel = (C[:, 1] >= rib["y"][0]) & (C[:, 1] <= rib["y"][1]) & ((C[:, 2] < 100) if rib["lower"] else (C[:, 2] > 150))
    idx = np.where(sel)[0]; rings = []
    for n, i in enumerate(idx):
        t, w, u = frame(C, i, oriented=True); a = math.radians(rib["angle"])
        hit, nrm = cast(T, C[i], w * math.cos(a) + u * math.sin(a)); c = hit + nrm * (rib["r"] - rib["sink"])
        q = n / max(len(idx) - 1, 1); r = rib["r"] * min(1.0, 4 * q, 4 * (1 - q)) ** 0.5 + 0.2
        side = np.cross(t, nrm)
        rings.append([bm.verts.new(c + (nrm * math.cos(b) + side * math.sin(b)) * r) for b in np.linspace(0, 2 * math.pi, K, endpoint=False)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(K): bm.faces.new((r0[k], r0[(k + 1) % K], r1[(k + 1) % K], r1[k]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("ribs_r"); bm.to_mesh(me)
for p in me.polygons: p.use_smooth = True
sc.collection.objects.link(bpy.data.objects.new("ribs_r", me))
ml = me.copy(); ml.name = "ribs_l"; ml.transform(Matrix.Scale(-1, 4, (1, 0, 0))); ml.flip_normals()
sc.collection.objects.link(bpy.data.objects.new("ribs_l", ml))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("RIBS ok")
