import bpy, bmesh, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body"
F = json.load(open(f"{D}/blades.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/body_v2.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in F]: bpy.data.objects.remove(o)
bb = bmesh.new(); bb.from_mesh(sc.objects["corp"].data); tree = BVHTree.FromBMesh(bb)
N = 40; SINK = 2.0
def blade(bm, p, side):
    (x0, z0), (x1, z1) = p["from"], p["to"]
    rows = []
    for i in range(N + 1):
        t = i / N; x = (x0 + (x1 - x0) * t) * side; z = z0 + (z1 - z0) * t
        hit, nrm, _, _ = tree.ray_cast(Vector((x, -2000, z)), Vector((0, 1, 0)), 4000)
        if hit is None: continue
        rows.append((hit, nrm))
    sec = []
    for i, (pt, nrm) in enumerate(rows):
        t = i / (len(rows) - 1)
        tan = (rows[min(i + 1, len(rows) - 1)][0] - rows[max(i - 1, 0)][0]).normalized()
        sidev = tan.cross(nrm).normalized()
        h = p["height"] * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.7 if t < 0.87 else p["height"] * max(0.0, (1 - t) / 0.13) * 0.9
        w = p["thick"] * (1 - 0.7 * t)
        sec.append([bm.verts.new(pt - nrm * SINK - sidev * w), bm.verts.new(pt + nrm * max(h, 0.3)), bm.verts.new(pt - nrm * SINK + sidev * w)])
    for a, b in zip(sec, sec[1:]):
        for j in range(3):
            bm.faces.new((a[j], b[j], b[(j + 1) % 3], a[(j + 1) % 3]))
    for ring, flip in ((sec[0], True), (sec[-1], False)):
        bm.faces.new(ring if not flip else list(reversed(ring)))
for name, p in F.items():
    if name.startswith("_"): continue
    bm = bmesh.new()
    for side in ((1,) if p.get("centre") else (1, -1)): blade(bm, p, side)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me)
    sc.collection.objects.link(bpy.data.objects.new(name, me))
bpy.data.libraries.write(f"{D}/body_v2.blend", {sc}, fake_user=True)
print("BLADES ok")
