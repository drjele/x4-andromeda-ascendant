# The board cleaned (asked: only the reference model, the assembled guides and our assembled pieces): every collection but KEEP
# removed with its objects (objects also linked in a kept collection stay), the assembled pieces (ASAMBLAT_NOU) moved by DX to the old
# board's place, unused data purged.
# Usage: blender -b <f.blend> --python curata_plansa.py -- <out.blend> <dx for ASAMBLAT_NOU> <collection to keep> ...
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; OUT, DX, KEEP = a[0], float(a[1]), set(a[2:])
keep_obs = {o for c in bpy.data.collections if c.name in KEEP for o in c.all_objects}
for c in list(bpy.data.collections):
    if c.name in KEEP: continue
    for o in list(c.objects):
        if o not in keep_obs: bpy.data.objects.remove(o)
    bpy.data.collections.remove(c)
for o in list(bpy.context.scene.collection.objects):
    if o not in keep_obs: bpy.data.objects.remove(o)
for o in bpy.data.collections["ASAMBLAT_NOU"].objects: o.location.x += DX
for _ in range(3): bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
print("PLANSA: colectii", [c.name for c in bpy.data.collections], "obiecte", len(bpy.data.objects)); bpy.ops.wm.save_as_mainfile(filepath=OUT)
