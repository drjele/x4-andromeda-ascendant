# Oval domes sitting on the body: each top point is lifted from the body surface below it.
import bpy, bmesh, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body"
F = json.load(open(f"{D}/domes.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/body_v2.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in F]: bpy.data.objects.remove(o)
body = sc.objects["corp"]; bb = bmesh.new(); bb.from_mesh(body.data); tree = BVHTree.FromBMesh(bb)
SINK = 3.0; NR, NA = 32, 72
BLEND = 1.35
for name, p in F.items():
    if name.startswith("_"): continue
    bm = bmesh.new(); rings = []
    for i in range(NR + 1):
        r = BLEND * i / NR
        row = []
        for k in range(NA):
            a = 2 * math.pi * k / NA; c, s = math.cos(a), math.sin(a)
            ox = p["half_wid"] * r * math.copysign(abs(c) ** (2 / p["outline_n"]), c)
            oy = p["half_len"] * r * math.copysign(abs(s) ** (2 / p["outline_n"]), s)
            down = -1 if not p.get("under") else 1
            if p.get("behind"):
                hit, nrm, _, _ = tree.ray_cast(Vector((ox, -3000, p["z"] + oy)), Vector((0, 1, 0)), 6000)
                if hit is None: hit, nrm = Vector((ox, -780, p["z"] + oy)), Vector((0, -1, 0))
                lift = p["height"] * (1 - min(1.0, BLEND * i / NR / BLEND) ** p["profile_n"]) ** 2 if i < NR else -SINK
                row.append(bm.verts.new(hit + Vector((0, -1, 0)) * lift)); continue
            hit, nrm, _, _ = tree.ray_cast(Vector((ox, p["y"] + oy, -2000 * down)), Vector((0, 0, down)), 4000)
            if hit is None: hit, nrm = Vector((ox, p["y"] + oy, 0)), Vector((0, 0, 1))
            # flat-topped core, then a tangent fillet that fades into the body by r = BLEND
            core = max(0.0, 1 - r ** p["profile_n"]) ** (1 / p["profile_n"]) if r < 1 else 0.0
            u = min(1.0, r / BLEND); fade = (1 - u * u) ** 2
            lift = p["height"] * (1 - u ** p["profile_n"]) ** 2 - SINK * u ** 8
            row.append(bm.verts.new(hit + Vector((0, 0, lift * -down))))
        rings.append(row)
    top = bm.verts.new(rings[0][0].co)
    for k in range(NA): bm.faces.new((top, rings[1][k], rings[1][(k + 1) % NA]))
    for a, b in zip(rings[1:], rings[2:]):
        for k in range(NA): bm.faces.new((a[k], b[k], b[(k + 1) % NA], a[(k + 1) % NA]))
    for v in rings[0]:
        if v is not top and not v.link_faces: bm.verts.remove(v)
    bm.normal_update()
    bm.faces.ensure_lookup_table()
    if p.get("behind"):
        if bm.faces[0].normal.y > 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    elif (bm.faces[0].normal.z < 0) != bool(p.get("under")): bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me)
    for pp in me.polygons: pp.use_smooth = True
    sc.collection.objects.link(bpy.data.objects.new(name, me))
bpy.data.libraries.write(f"{D}/body_v2.blend", {sc}, fake_user=True)
print("DOMES ok")
