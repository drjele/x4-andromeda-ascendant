# Scales along the outer underside of each lower arm: overlapping leaves, each rooted in the arm at its
# front and lifting off toward its back edge, like shingles pointing aft.
import bpy, bmesh, json, math, sys
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
sys.path.insert(0, f"{D}/arms"); from a_frame import member, frame, cast
A = json.load(open(f"{D}/arms/a_params.json"))["members"]["arm"]; S = json.load(open(f"{D}/arms/a_deco.json"))["scales"]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in ("scales_r", "scales_l")]: bpy.data.objects.remove(o)
b = bmesh.new(); b.from_mesh(sc.objects["arm_r"].data); T = BVHTree.FromBMesh(b)
C, f, W, H, R = member(A)
front = (C[:, 1] > -700) & (C[:, 2] < -100)
bm = bmesh.new()
for y in np.linspace(*S["y"], S["count"]):
    i = np.where(front)[0][np.argmin(np.abs(C[front, 1] - y))]
    t, w, u = frame(C, i, oriented=True); a = math.radians(S["angle"])
    p, n = cast(T, C[i], w * math.cos(a) + u * math.sin(a))          # rooted on the built arm, not the ideal section
    back = -t if t[1] > 0 else t; back = back - n * back.dot(n); back /= np.linalg.norm(back); side = np.cross(n, back)
    L, R = S["length"], S["width"] / 2; rows = []
    for k in range(13):
        q = k / 12; hw = R * min(1.0, 3.0 * q) ** 0.5 * (1 - q) ** 0.6 + 0.3
        lift = -S["sink"] + S["lift"] * q * q
        row = []
        for j in range(9):
            v = -1 + 2 * j / 8; c = p + back * (q * L - 0.25 * L) + side * v * hw + n * (lift - 0.15 * S["lift"] * v * v)
            row.append((bm.verts.new(c + n * S["thick"] / 2 * (1 - abs(v) ** 4) * (1 - q) ** 0.3), bm.verts.new(c - n * S["thick"] / 2 * (1 - abs(v) ** 4) * (1 - q) ** 0.3)))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(8):
            bm.faces.new((r0[j][0], r0[j + 1][0], r1[j + 1][0], r1[j][0])); bm.faces.new((r0[j][1], r1[j][1], r1[j + 1][1], r0[j + 1][1]))
        for j in (0, 8): bm.faces.new((r0[j][0], r1[j][0], r1[j][1], r0[j][1]))
    for r in (rows[0], rows[-1]):
        for j in range(8): bm.faces.new((r[j][0], r[j][1], r[j + 1][1], r[j + 1][0]))
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.05); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("scales_r"); bm.to_mesh(me)
for pp in me.polygons: pp.use_smooth = True
sc.collection.objects.link(bpy.data.objects.new("scales_r", me))
ml = me.copy(); ml.name = "scales_l"; ml.transform(Matrix.Scale(-1, 4, (1, 0, 0))); ml.flip_normals()
sc.collection.objects.link(bpy.data.objects.new("scales_l", ml))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("SCALES ok")
