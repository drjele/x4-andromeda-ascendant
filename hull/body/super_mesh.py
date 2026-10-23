import bpy, bmesh, json
from mathutils import Vector
R = json.load(open("/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body/super_rings.json")); ANG = len(R[0])
bpy.ops.wm.open_mainfile(filepath="/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/seg/source.blend")
sc = bpy.data.scenes["seg"]
bm = bmesh.new(); vs = []
for ring in R:
    pts = [Vector(p) for p in ring]
    if max((p - pts[0]).length for p in pts) < 0.5: vs.append([bm.verts.new(pts[0])])
    else: vs.append([bm.verts.new(p) for p in pts])
for a, b in zip(vs, vs[1:]):
    for k in range(ANG):
        if len(a) == 1: bm.faces.new((a[0], b[(k + 1) % ANG], b[k]))
        elif len(b) == 1: bm.faces.new((a[k], a[(k + 1) % ANG], b[0]))
        else: bm.faces.new((a[k], a[(k + 1) % ANG], b[(k + 1) % ANG], b[k]))
bm.normal_update(); bm.faces.ensure_lookup_table()
mid = bm.faces[len(bm.faces) // 2]; centre = Vector((0, mid.calc_center_median().y, mid.calc_center_median().z))
if mid.normal.dot(mid.calc_center_median() - centre) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("corp"); bm.to_mesh(me)
for p in me.polygons: p.use_smooth = True
ob = bpy.data.objects.new("corp", me); sc.collection.objects.link(ob)
bpy.data.libraries.write("/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body/body.blend", {sc}, fake_user=True)
print("BODY", len(me.polygons))
