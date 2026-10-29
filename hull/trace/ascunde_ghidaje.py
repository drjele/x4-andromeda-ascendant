# Guides out of the way (asked: "ascunde toate ghidajele, să fie mai curat"): every collection named GHIDAJE* excluded from
# the view layer (kept in the file, back with one tick). Usage: blender -b <f.blend> --python ascunde_ghidaje.py -- <out.blend>
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]
def walk(lc):
    for c in lc.children:
        if c.name.startswith("GHIDAJE"): c.exclude = True; print("ASCUNS", c.name, len(c.collection.all_objects))
        walk(c)
walk(bpy.context.view_layer.layer_collection); bpy.ops.wm.save_as_mainfile(filepath=OUT)
