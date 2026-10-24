# The cyan nacelle along the nose of the U arch: a crescent housing on the front face, tallest at the nose and
# tapering along the flanks, with a recessed, key-ribbed slot; cast horizontally onto the built arch around its centre.
import bpy, bmesh, json, math, sys
import numpy as np
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
sys.path.insert(0, f"{D}/arms"); from a_frame import cast, housing, grid_mesh
N = json.load(open(f"{D}/uarch/g_params.json"))["nacelle"]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name == "uarch_nacelle"]: bpy.data.objects.remove(o)
b = bmesh.new(); b.from_mesh(sc.objects["uarch"].data); T = BVHTree.FromBMesh(b)
cy, cz = N["center"]; re = N["radius"]; M = 14
th = np.radians(np.arange(N["theta"][0] - 8, N["theta"][1] + 8.1, 1.2)); zs = np.arange(cz - N["half"][0] - M, cz + N["half"][0] + M, 1.5)
TH, Z = np.meshgrid(th, zs); A = TH * re
def crescent(h, tmax):
    u = np.clip(np.abs(TH) / math.radians(tmax), 0, 1); return h[0] + (h[1] - h[0]) * u * u
hh, hs = crescent(N["half"], N["theta"][1]), crescent(N["slot"]["half"], N["slot"]["theta"][1])
spec = dict(N, x=[math.radians(N["theta"][0]) * re, math.radians(N["theta"][1]) * re], y=[cz - hh, cz + hh],
            slot=dict(N["slot"], x=[math.radians(N["slot"]["theta"][0]) * re, math.radians(N["slot"]["theta"][1]) * re], y=[cz - hs, cz + hs]))
L = housing(A, Z, spec, keys_axis=A)
bm = bmesh.new(); G = {}
for i, z in enumerate(zs):
    for j, a in enumerate(th):
        o = np.array([700 * math.sin(a), cy + 700 * math.cos(a), z]); hit, nrm = cast(T, o, np.array([0, cy, z]) - o, 800)
        if hit is not None: G[(i, j)] = bm.verts.new(hit + nrm * float(L[i, j]))
grid_mesh(bm, G, len(zs), len(th), keep=L > 0)
for _ in range(2): bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if not v.is_boundary], factor=0.3, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("uarch_nacelle"); bm.to_mesh(me)
for p in me.polygons: p.use_smooth = True
sc.collection.objects.link(bpy.data.objects.new("uarch_nacelle", me))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("UNACELLE ok", len(me.polygons))
