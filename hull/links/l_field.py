# Measure the side link (wing) of the source from above: its top and the surface right under it.
import bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath="/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/vtop/vsrc.blend" if False else "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]
b = bmesh.new(); b.from_mesh(sc.objects["source"].data); S = BVHTree.FromBMesh(b)
b2 = bmesh.new(); b2.from_mesh(sc.objects["corp"].data); C = BVHTree.FromBMesh(b2)
xs = np.arange(100, 761, 5.0); ys = np.arange(-700, 381, 5.0)
top = np.full((len(ys), len(xs)), np.nan); bot = top.copy(); cw = np.full(len(ys), np.nan)
for i, y in enumerate(ys):
    h = C.ray_cast(Vector((1000, y, -60)), Vector((-1, 0, 0)), 2000)[0]
    if h is not None: cw[i] = h.x
    for j, x in enumerate(xs):
        zs = []; o = Vector((x, y, 160))
        while len(zs) < 6:
            h = S.ray_cast(o, Vector((0, 0, -1)), 600)[0]
            if h is None or h.z < -420: break
            zs.append(h.z); o = h - Vector((0, 0, 0.05))
        if len(zs) >= 2:
            top[i, j] = zs[0]
            for z in zs[1:]:
                if zs[0] - z > 4: bot[i, j] = z; break
np.savez("/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/links/lfield.npz", xs=xs, ys=ys, top=top, bot=bot, body_x=cw)
print("LFIELD ok")
