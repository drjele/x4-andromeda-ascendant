# Batteries of horizontal slats on the bare body flank beside the nose: thin straight blades standing out
# from the hull, stacked in height with gaps, each set into the body with a sunk base and rounded ends.
import bpy, bmesh, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body"
F = json.load(open(f"{D}/slats.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/body_v2.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in F]: bpy.data.objects.remove(o)
bb = bmesh.new(); bb.from_mesh(sc.objects["corp"].data); tree = BVHTree.FromBMesh(bb)
SINK = 5.0; N = 48
def fin(bm, p, z, side):
    rows = []
    for i in range(N + 1):
        y = p["y"][0] + (p["y"][1] - p["y"][0]) * i / N
        hit, nrm, _, _ = tree.ray_cast(Vector((0, y, z)), Vector((side, 0, 0)), 2000)
        if hit is not None: rows.append((hit, nrm))
    sec = []; out = sum((n for _, n in rows), Vector()).normalized(); up = Vector((0, 0, 1))   # one direction for the whole blade, so it stays straight
    for i, (pt, nrm) in enumerate(rows):
        t = i / (len(rows) - 1); h = p["reach"] * min(1.0, 5 * t, 5 * (1 - t)) ** 0.5; w = p["thick"] / 2; b = w + p["base"]
        sec.append([bm.verts.new(pt - nrm * SINK - up * b), bm.verts.new(pt + out * h - up * w), bm.verts.new(pt + out * h + up * w), bm.verts.new(pt - nrm * SINK + up * b)])
    for a, c in zip(sec, sec[1:]):
        for j in range(4): bm.faces.new((a[j], c[j], c[(j + 1) % 4], a[(j + 1) % 4]))
    bm.faces.new(sec[0][::-1]); bm.faces.new(sec[-1])
for name, p in F.items():
    if name.startswith("_"): continue
    bm = bmesh.new()
    for side in (1, -1):
        for z in p["z"]: fin(bm, p, z, side)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me)
    for pp in me.polygons: pp.use_smooth = True
    sc.collection.objects.link(bpy.data.objects.new(name, me))
bpy.data.libraries.write(f"{D}/body_v2.blend", {sc}, fake_user=True)
print("SLATS ok")
