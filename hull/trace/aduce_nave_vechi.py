# Older ships brought back onto the board beside the current work, each in its own collection, names prefixed, moved rigidly along X only.
# Usage: blender -b <in.blend> --python aduce_nave_vechi.py -- <out.blend> <src.blend>:<collection or object regex>:<new collection>:<prefix>:<x centre> ...
import bpy, sys, re
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]
for spec in a[1:]:
    src, sel, cn, pf, xc = spec.rsplit(":", 4); xc = float(xc)
    with bpy.data.libraries.load(src, link=False) as (fr, to):
        if sel.startswith("COL="): to.collections = [sel[4:]]
        else: to.objects = [n for n in fr.objects if re.search(sel, n)]
    obs = [o for c in to.collections for o in c.all_objects] if sel.startswith("COL=") else list(to.objects)
    col = bpy.data.collections.new(cn); bpy.context.scene.collection.children.link(col)
    for o in obs:
        o.name = pf + o.name.split(".0")[0] if not o.name.startswith(pf) else o.name
        for uc in list(o.users_collection): uc.objects.unlink(o)
        col.objects.link(o)
    for c in to.collections: bpy.data.collections.remove(c)
    bpy.context.view_layer.update()                                                     # appended objects: world matrices are stale until the scene is evaluated
    p = [o.matrix_world @ Vector(b) for o in obs if o.type == "MESH" for b in o.bound_box]; cx = (min(q.x for q in p) + max(q.x for q in p)) / 2
    for o in obs:
        if o.parent is None: o.location.x += xc - cx
    print("ADUS", cn, len(obs), "obiecte, centrul x %.0f -> %.0f" % (cx, xc))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SALVAT", OUT)
