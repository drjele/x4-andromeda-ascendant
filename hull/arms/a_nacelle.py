# The cyan housing on the outer flank of each lower arm (ref 12, the lower-outer corner of each loop): a low
# rounded housing with a recessed, key-ribbed slot, cast onto the built strap from its path.
import bpy, bmesh, json, math, sys
import numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
sys.path.insert(0, f"{D}/arms"); from a_frame import member, frame, cast, housing, grid_mesh
P = json.load(open(f"{D}/arms/a_params.json")); N = json.load(open(f"{D}/arms/a_deco.json"))["nacelle"]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in ("nacelle_r", "nacelle_l")]: bpy.data.objects.remove(o)
b = bmesh.new(); b.from_mesh(sc.objects["arm_r"].data); T = BVHTree.FromBMesh(b)
C, f, W, H, R = member(P["members"]["arm"], 40); M = 16
idx = np.where((f >= N["f"][0]) & (f <= N["f"][1]))[0]
s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C[idx], axis=0), axis=1))]; s -= s[-1] / 2
re = (W[idx] + H[idx]).mean() / 4                                   # metres per radian across the band
ang = np.radians(np.arange(N["angle"][0], N["angle"][1] + 0.1, 1.5)); am = np.radians(sum(N["angle"]) / 2)
S, A = np.meshgrid(s, (ang - am) * re)
sf = lambda ff: np.interp(ff, f[idx], s); av = lambda a: (math.radians(a) - am) * re
spec = {"x": [s[0] + M, s[-1] - M], "y": [av(N["angle"][0]) + M, av(N["angle"][1]) - M], "lift": N["lift"], "rim": N["rim"], "keys": N["keys"],
        "slot": {"x": [sf(N["slot"]["f"][0]), sf(N["slot"]["f"][1])], "y": [av(N["slot"]["angle"][0]), av(N["slot"]["angle"][1])], "depth": N["slot"]["depth"], "rim": N["slot"]["rim"]}}
L = housing(S, A, spec, keys_axis=S)
bm = bmesh.new(); G = {}
for i, a in enumerate(ang):
    for j, k in enumerate(idx):
        t, w, u = frame(C, k, oriented=True); hit, nrm = cast(T, C[k], w * math.cos(a) + u * math.sin(a))
        if hit is not None: G[(i, j)] = bm.verts.new(hit + nrm * float(L[i, j]))
grid_mesh(bm, G, len(ang), len(idx), keep=L > 0)
for _ in range(2): bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if not v.is_boundary], factor=0.3, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("nacelle_r"); bm.to_mesh(me)
for p in me.polygons: p.use_smooth = True
sc.collection.objects.link(bpy.data.objects.new("nacelle_r", me))
ml = me.copy(); ml.name = "nacelle_l"; ml.transform(Matrix.Scale(-1, 4, (1, 0, 0))); ml.flip_normals()
sc.collection.objects.link(bpy.data.objects.new("nacelle_l", ml))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("NACELLE ok", len(me.polygons))
