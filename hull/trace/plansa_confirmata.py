# The board with only what is confirmed (asked: the reference model, the confirmed guides assembled and the real confirmed
# pieces assembled - only that): keeps REFERINTA, GHIDAJE_ASAMBLATE and PIESE_DIN_GHIDAJE_ASAMBLAT; the front arms and red
# nacelles (BRATE_FATA_CONFIRMATE, meshes in the old x -1700 frame) moved by DX into the assembled block; everything else
# (objects and collections) removed, orphan data purged.
# Usage: blender -b <in> --python plansa_confirmata.py -- <out.blend> [DX=-7700]
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; DX = float(a[1]) if len(a) > 1 else -7700.0
KEEP = ("REFERINTA", "GHIDAJE_ASAMBLATE", "PIESE_DIN_GHIDAJE_ASAMBLAT"); dst = bpy.data.collections["PIESE_DIN_GHIDAJE_ASAMBLAT"]
for o in list(bpy.data.collections["BRATE_FATA_CONFIRMATE"].objects):
    o.location.x += DX
    for c in o.users_collection: c.objects.unlink(o)
    dst.objects.link(o)
keep = {o.name for c in KEEP for o in bpy.data.collections[c].all_objects}
gone = [o.name for o in bpy.data.objects if o.name not in keep]
for n in gone: bpy.data.objects.remove(bpy.data.objects[n])
for c in [c for c in bpy.data.collections if c.name not in KEEP]: bpy.data.collections.remove(c)
for c in KEEP: bpy.data.collections[c].hide_viewport = False; bpy.data.collections[c].hide_render = False
bpy.data.orphans_purge(do_recursive=True)
for c in KEEP: print("PASTRAT %-28s %4d obiecte" % (c, len(bpy.data.collections[c].all_objects)))
print("STERSE %d obiecte; colectii ramase: %s" % (len(gone), [c.name for c in bpy.data.collections]))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
