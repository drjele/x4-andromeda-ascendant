# The blade's retracted (stowed) state for a preview (asked: blades slide out of the red nacelles' thin edge; try both blade shapes):
# a copy of the blade with every vertex moved by the slide vector of its nearest station - variant "after the nacelle": the per-
# station vector from <param>_param.npz (back along the nacelle's V axis by the blade's depth); variant "current blade": back across
# the arm (-U) by SB m. Not yet the game parts (those will be rigid segments); just where it ends up.
# Usage: blender -b <in.blend> --python lama_strans.py -- <out.blend> <obj> <param npz> <base key|slide> [SB] ; X0=-1600
import bpy, sys, os, numpy as np
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT, OBJ, PRM, KEY = a[:4]; SB = float(a[4]) if len(a) > 4 else 0; X0 = float(os.environ.get("X0", -1600))
Pm = np.load(PRM)
if KEY == "slide": base, vec = Pm["thin_edge"], Pm["slide"]
else: base, vec = Pm["base"], -Pm["U"] * SB
src = bpy.data.objects[OBJ]; me = src.data.copy(); mir = OBJ.endswith("_D")
kd = KDTree(len(base))
for i, p in enumerate(base): kd.insert(p * ([-1, 1, 1] if mir else 1), i)
kd.balance()
for v in me.vertices:
    i = kd.find(v.co)[1]; dv = vec[i] * ([-1, 1, 1] if mir else 1); v.co.x += dv[0]; v.co.y += dv[1]; v.co.z += dv[2]
nm = OBJ + "_strans"
if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm])
o = bpy.data.objects.new(nm, me); o.location = src.location
for c in src.users_collection: c.objects.link(o)
print("STRANS %s: deplasare max %.1f m" % (nm, np.linalg.norm(vec, axis=1).max())); bpy.ops.wm.save_as_mainfile(filepath=OUT)
