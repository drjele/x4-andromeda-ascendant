# Candidate blade hinges marked on the ship (asked: the hinge "at the middle of an_brat_fata_S seen from +/-Z" - show the tried
# places so the right one can be pointed at): numbered vertical bars (12 m thick, 120 m tall) at each point, the open blade
# an_lama_S, ship grey; removes the stowed previews; renders a top view (orthographic) with the numbers drawn on.
# Usage: blender -b <in.blend> --python balamale_marcate.py -- <out.blend> <out.png> <x:y:label,...>
import bpy, sys, bmesh
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, PNG = a[0], a[1]; PTS = [(float(q.split(":")[0]), float(q.split(":")[1]), q.split(":")[2]) for q in a[2].split(",")]
for n in [o.name for o in bpy.data.objects if o.name.startswith(("lama_stransa_", "balama_lama_", "marcaj_balama_"))]: bpy.data.objects.remove(bpy.data.objects[n])
col = bpy.data.collections.get("BALAMALE_INCERCATE") or bpy.data.collections.new("BALAMALE_INCERCATE")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
sc = bpy.context.scene
for x, y, lab in PTS:
    me = bpy.data.meshes.new("marcaj_balama_" + lab); bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=6, radius2=6, depth=120); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("marcaj_balama_" + lab, me); o.location = (x - 1600, y, 300); o.color = (0, .9, 1, 1); col.objects.link(o)
    t = bpy.data.curves.new("eticheta_" + lab, "FONT"); t.body = lab; t.size = 40; to = bpy.data.objects.new("eticheta_" + lab, t); to.location = (x - 1600 + 12, y + 12, 420); to.color = (0, 1, 1, 1); col.objects.link(to)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
sh = sc.display.shading; sc.render.engine = "BLENDER_WORKBENCH"; sh.light = "STUDIO"; sh.color_type = "OBJECT"; sh.show_cavity = True
for o in sc.objects: o.hide_render = not (o.users_collection and (o.users_collection[0].name in ("ASAMBLAT_NOU", "BALAMALE_INCERCATE")))
for o in bpy.data.collections["ASAMBLAT_NOU"].objects: o.color = (.72, .72, .75, 1)
bpy.data.objects["an_lama_S"].color = (1, .85, 0, 1); bpy.data.objects["an_lama_D"].color = (1, .85, 0, 1)
sc.render.resolution_x, sc.render.resolution_y = 1400, 1400
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.type = "ORTHO"; cam.ortho_scale = 1150; cam.clip_end = 50000
co.location = (-1600 - 330, 420, 3000); co.rotation_euler = (0, 0, 0)
sc.render.filepath = PNG; bpy.ops.render.render(write_still=True); print("MARCAT", len(PTS))
