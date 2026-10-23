import bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath="/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/vtop/v_scene.blend")
b = bmesh.new(); b.from_mesh(bpy.data.scenes["seg"].objects["source"].data); T = BVHTree.FromBMesh(b)
for z in range(160, 311, 15):
    row = []
    for y in range(-720, -279, 30):
        hs = []; o = Vector((40, y, z))
        while len(hs) < 6:
            h = T.ray_cast(o, Vector((1, 0, 0)), 300)[0]
            if h is None or h.x > 260: break
            hs.append(round(h.x)); o = h + Vector((0.05, 0, 0))
        row.append(f"{y}:{hs[:2]}" if hs else f"{y}:-")
    print(z, " ".join(row))
