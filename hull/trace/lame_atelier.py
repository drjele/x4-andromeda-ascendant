# Blade workshop beside the ship (asked: put all the reference blades apart, run them through our clean-up, copy the arms and PS too,
# and iterate until they animate right): collection ATELIER_LAME at x XB holding copies (own mesh data) of an_PS, an_PS_rama,
# an_brat_fata_S/D, an_nacela_*_S/D, an_brat_spate_S/D, an_ureche_S/D and of every reference blade Circle.* (S half kept, named
# ref_lama_<nr>_S). Everything in ship coordinates + XB on x. Usage: blender -b <in.blend> --python lame_atelier.py -- <out.blend> ; env XB=-7000
import bpy, bmesh, sys, os
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]; XB = float(os.environ.get("XB", -7000))
old = bpy.data.collections.get("ATELIER_LAME")
if old:
    for o in list(old.objects): bpy.data.objects.remove(o)
    bpy.data.collections.remove(old)
col = bpy.data.collections.new("ATELIER_LAME"); bpy.context.scene.collection.children.link(col)
hosts = [o.name for o in bpy.data.collections["ASAMBLAT_NOU"].objects if o.type == "MESH" and not o.name.startswith("an_lama")]   # every ship piece (the hiding check needs them all)
for n in hosts:
    s = bpy.data.objects[n]; me = s.data.copy(); me.transform(Matrix.Translation(Vector((1600, 0, 0))) @ s.matrix_world)   # mesh in ship coords
    o = bpy.data.objects.new("at_" + n[3:], me); o.location = Vector((XB, 0, 0)); col.objects.link(o)
for s in sorted([o for o in bpy.data.objects if o.name.startswith("Circle") and o.type == "MESH"], key=lambda q: q.name):
    bm = bmesh.new(); bm.from_mesh(s.data); bm.transform(s.matrix_world)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x > 0.01], context="VERTS")
    me = bpy.data.meshes.new("ref_lama_" + s.name.split(".")[1] + "_S"); bm.to_mesh(me); bm.free()
    for m in s.data.materials: me.materials.append(m)
    o = bpy.data.objects.new(me.name, me); o.location = Vector((XB, 0, 0)); col.objects.link(o)
print("ATELIER la x %.0f: %d obiecte" % (XB, len(col.objects))); bpy.ops.wm.save_as_mainfile(filepath=OUT)
