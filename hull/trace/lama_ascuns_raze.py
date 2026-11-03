# Is the stowed blade hidden - by rays, not pixels (the pixel count was wrong: the colour transform pushed the red under the
# threshold): a blade vertex is exposed if a ray from it up, down or along 4 obliques (45 deg) hits no ship piece (ASAMBLAT_NOU
# without the blades). For hinge (px, py, pz), each turn angle about the vertical and each slide distance along SLIDE.
# Usage: blender -b <f.blend> --python lama_ascuns_raze.py -- <px,py,pz> <angles a0:a1:s> <slides d0:d1:s> <slide x,y,z> ; env STEP=3
import bpy, sys, os, numpy as np, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; px, py, pz = (float(q) for q in a[0].split(","))
rng = lambda s: np.arange(*(lambda t: (t[0], t[1] + 1e-6, t[2]))([float(q) for q in s.split(":")])); ANGS, DS = rng(a[1]), rng(a[2])
sv = Vector([float(q) for q in a[3].split(",")]).normalized(); STEP = int(os.environ.get("STEP", 3))
ship = [o for o in bpy.data.collections["ASAMBLAT_NOU"].objects if not o.name.startswith(("an_lama", "lama")) and o.type == "MESH"]
V, F = [], []
for o in ship:
    b = len(V); V += [o.matrix_world @ v.co for v in o.data.vertices]; F += [[b + i for i in p.vertices] for p in o.data.polygons]
T = BVHTree.FromPolygons(V, F)
bl = bpy.data.objects[os.environ.get("OBJ", "an_lama_S")]; P0 = [bl.matrix_world @ v.co for v in bl.data.vertices][::STEP]; Pv = Vector((px - 1600, py, pz))
dirs = [Vector(d).normalized() for d in ((0, 0, 1), (0, 0, -1), (1, 0, 1), (-1, 0, 1), (0, 1, -1), (0, -1, -1))]
def exposed(M):
    n = 0
    for p in P0:
        q = M @ p
        if any(T.ray_cast(q + d * .3, d, 4000)[0] is None for d in dirs): n += 1
    return n / len(P0)
best = None
print("RAZE lama deschisa: expusa %.0f%%" % (100 * exposed(Matrix.Identity(4))))
for ang in ANGS:
    row = []
    for d in DS:
        M = Matrix.Translation(sv * d) @ Matrix.Translation(Pv) @ Matrix.Rotation(math.radians(ang), 4, "Z") @ Matrix.Translation(-Pv)
        f = exposed(M); row.append((d, f))
        if best is None or f < best[0]: best = (f, ang, d)
    print("RAZE rotire %+5.1f: " % ang + "  ".join("%.0f m:%.1f%%" % (q[0], 100 * q[1]) for q in row))
print("RAZE cel mai bun: rotire %+.1f, alunecare %.0f m -> expus %.1f%%" % (best[1], best[2], 100 * best[0]))
