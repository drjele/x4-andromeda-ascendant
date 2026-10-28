# The saved file opens looking at the new work, not at the reference ship: the 3D views centred on the given collection
# (or object-name prefix), zoomed to frame it, its first object selected and active; clip range wide enough for the ship.
# Usage: blender -b <file.blend> --python focus_view.py -- <collection_or_prefix>
import bpy, sys
from mathutils import Vector
T = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
c = bpy.data.collections.get(T); obs = [o for o in (c.all_objects if c else sc.objects) if o.type in ("MESH", "CURVE") and (c or o.name.startswith(T))]
pts = [o.matrix_world @ Vector(b) for o in obs for b in o.bound_box]; lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
for o in sc.objects: o.select_set(False)
obs[0].select_set(True); bpy.context.view_layer.objects.active = obs[0]
for scr in bpy.data.screens:
    for ar in scr.areas:
        for sp in ar.spaces:
            if sp.type == "VIEW_3D":
                sp.clip_start, sp.clip_end = 1.0, 100000.0
                r = sp.region_3d; r.view_location = (lo + hi) / 2; r.view_distance = (hi - lo).length * 1.2
bpy.ops.wm.save_mainfile(); print("FOCUS", T, len(obs), "obiecte, centru", [round(x) for x in (lo + hi) / 2])
