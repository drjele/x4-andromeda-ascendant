# Body half-width table bw(y, z): where a ray from outboard meets the clean body, for blending the links.
import bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath="/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body/body_v2.blend")
b = bmesh.new(); b.from_mesh(bpy.data.scenes["seg"].objects["corp"].data); C = BVHTree.FromBMesh(b)
ys = np.arange(-700, 381, 5.0); zs = np.arange(-260, 361, 5.0); bw = np.zeros((len(ys), len(zs)))
for i, y in enumerate(ys):
    for k, z in enumerate(zs):
        h = C.ray_cast(Vector((1500, y, z)), Vector((-1, 0, 0)), 3000)[0]
        bw[i, k] = h.x if h is not None else 0.0
np.savez("/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/links/lbody.npz", ys=ys, zs=zs, bw=bw)
print("LBODY ok")
