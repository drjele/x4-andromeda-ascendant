# Freeze the working scene as a named version: every built piece (not the original) copied into one collection
# written to versions/<name>.blend. Usage: blender -b --python freeze.py -- V1
import bpy, sys
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"; name = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]
col = bpy.data.collections.new(name)
for o in [o for o in sc.objects if o.type == "MESH" and not o.name.startswith("source")]:
    c = o.copy(); c.data = o.data.copy(); c.name = f"{name}_{o.name}"; c.data.name = c.name; col.objects.link(c)
bpy.data.libraries.write(f"{D}/versions/{name}.blend", {col}, fake_user=True); print("FROZEN", name, len(col.objects))
