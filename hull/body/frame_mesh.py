import bpy, bmesh, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body"
F = json.load(open(f"{D}/frames.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/body_v2.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in F]: bpy.data.objects.remove(o)
bb = bmesh.new(); bb.from_mesh(sc.objects["corp"].data); tree = BVHTree.FromBMesh(bb)
NP, NT = 120, 16
for name, p in F.items():
    if name.startswith("_"): continue
    path = []
    for k in range(NP):
        a = 2 * math.pi * k / NP; c, s = math.cos(a), math.sin(a)
        x = p["half_w"] * math.copysign(abs(c) ** (2 / p["n"]), c); z = p["z"] + p["half_h"] * math.copysign(abs(s) ** (2 / p["n"]), s)
        hit, nrm, _, _ = tree.ray_cast(Vector((x, -2000, z)), Vector((0, 1, 0)), 4000)
        path.append((hit + nrm * p["offset"], nrm) if hit else (Vector((x, -785, z)), Vector((0, -1, 0))))
    # a band across the path, lifted as a smooth bump that fades into the hull on both sides
    bm = bmesh.new(); rows = []; NU = 14
    for k, (pt, nrm) in enumerate(path):
        t = (path[(k + 1) % NP][0] - path[k - 1][0]).normalized()
        side = t.cross(nrm).normalized()
        row = []
        for j in range(NU + 1):
            u = -1 + 2 * j / NU
            q = pt - nrm * p["offset"] + side * u * p["band"]
            hit, hn, _, _ = tree.ray_cast(q - nrm * 30 + nrm * 60, -nrm, 120)
            base = hit if hit else q
            lift = p["height"] * (1 - u * u) ** 2 - 1.5 * u ** 8
            row.append(bm.verts.new(base + nrm * lift))
        rows.append(row)
    for k in range(NP):
        a, b = rows[k], rows[(k + 1) % NP]
        for j in range(NU): bm.faces.new((a[j], a[j + 1], b[j + 1], b[j]))
    bm.normal_update(); bm.faces.ensure_lookup_table()
    f0 = bm.faces[NU // 2]
    if f0.normal.dot(path[0][1]) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me)
    for pp in me.polygons: pp.use_smooth = True
    sc.collection.objects.link(bpy.data.objects.new(name, me))
bpy.data.libraries.write(f"{D}/body_v2.blend", {sc}, fake_user=True)
print("FRAMES ok")
