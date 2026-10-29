# Pieces pulled apart (asked: explode them): each named object moved by its own offset (object location only, meshes
# untouched, so the assembled set elsewhere - PS_NOU - is unchanged and the offsets can be undone).
# Usage: blender -b <in> --python explodeaza.py -- <out.blend> <obj=dx,dy,dz ...>
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]
for s in a[1:]:
    n, d = s.split("="); o = bpy.data.objects[n]; o.location += Vector([float(q) for q in d.split(",")])
    print("EXPLODAT %-20s cu (%s)" % (n, d))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
