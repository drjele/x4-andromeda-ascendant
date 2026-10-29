# The visible guides welded into ONE object and hidden, not deleted (asked: hide the guides but keep them, joined in one
# piece). Every curve in the named collections joined into one curve object NAME in collection NAME (hidden, excluded
# from render); the old collections stay (empty). Usage: blender -b <in> --python sudeaza_ghidaje.py -- <out> <NAME> <COLL...>
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; OUT, NAME, COLLS = a[0], a[1], a[2:]
obs = [o for c in COLLS for o in bpy.data.collections[c].objects if o.type == "CURVE"]
for o in obs: o.hide_set(False); o.hide_viewport = False
bpy.ops.object.select_all(action="DESELECT")
for o in obs: o.select_set(True)
bpy.context.view_layer.objects.active = obs[0]; bpy.ops.object.join(); j = bpy.context.view_layer.objects.active; j.name = NAME
nc = bpy.data.collections.new(NAME); bpy.context.scene.collection.children.link(nc)
for c in list(j.users_collection): c.objects.unlink(j)
nc.objects.link(j)
if os.environ.get("SG_ASCUNDE", "1") == "1": j.hide_set(True); j.hide_render = True    # SG_ASCUNDE=0 keeps it visible
print("GHIDAJE SUDATE: %d curbe din %s -> 1 obiect %s (%d linii), %s" % (len(obs), ", ".join(COLLS), NAME, len(j.data.splines), "ascuns" if j.hide_get() else "vizibil"))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
