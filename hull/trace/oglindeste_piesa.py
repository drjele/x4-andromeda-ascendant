# A piece mirrored to the other side (x -> -x about the ship's axis, normals flipped), into the same collection, for the
# assembled (gp_) and exploded (gpe_) copies; the old source object of the other side (if named) removed - it is now in place.
# Usage: blender -b <in> --python oglindeste_piesa.py -- <out.blend> <base name e.g. comp_055> <from side S|D> [old object to remove]
import bpy, bmesh, sys
a = sys.argv[sys.argv.index("--") + 1:]; OUT, B, FR = a[0], a[1], a[2]; TO = "D" if FR == "S" else "S"
for pre in ("gp_", "gpe_"):
    src = bpy.data.objects[pre + B + "_" + FR]; ref = bpy.data.objects[pre + "PS"]; n = pre + B + "_" + TO
    o0 = bpy.data.objects.get(n)
    if o0: bpy.data.objects.remove(o0)
    me = src.data.copy(); me.name = n; bm = bmesh.new(); bm.from_mesh(me)
    for v in bm.verts: v.co.x = -v.co.x
    bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(n, me); src.users_collection[0].objects.link(o)
    o.location = src.location.copy(); o.location.x = ref.location.x - (src.location.x - ref.location.x)
    print("OGLINDIT %s -> %s, x %.0f" % (src.name, n, o.location.x))
if len(a) > 3 and bpy.data.objects.get(a[3]):
    c = bpy.data.objects[a[3]].users_collection[0]; bpy.data.objects.remove(bpy.data.objects[a[3]]); print("SCOS", a[3])
    if not c.objects and not c.children: bpy.data.collections.remove(c); print("COLECTIE GOALA STEARSA")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
