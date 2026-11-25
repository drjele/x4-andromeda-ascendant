# Confirmed data in one place: keeps one collection of a scene, saves it as its own .blend and writes a hash per object
# (mesh coordinates + polygon indices + world matrix), so a later scene can be checked against it (confirmat_verifica.py).
# Usage: blender -b <scene> --python confirmat_blend.py -- <collection> <out.blend> <out.json>
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from confirmat_hash import hash_col
COL, OUT, JS = sys.argv[sys.argv.index("--") + 1:][:3]
assert not os.path.exists(OUT), OUT
H = hash_col(COL); json.dump(dict(scena=bpy.data.filepath, colectie=COL, obiecte=H), open(JS, "w"), indent=1)
keep = {o.name for o in bpy.data.collections[COL].all_objects}
for o in list(bpy.data.objects):
    if o.name not in keep: bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    if c.name != COL and not c.all_objects: bpy.data.collections.remove(c)
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, copy=True)
print("CONFIRMAT", COL, len(H), "obiecte ->", OUT)
