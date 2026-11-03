# Blade check against the static nacelles and the arm (asked: the blade leaves the arm a little lower, under the nacelle, not through
# it; the nacelles do not move): for the blade piece OBJ built deployed, triangle pairs it shares with an_nacela_inchis_S /
# an_nacela_deschis_S (must be 0) and with an_brat_fata_S (where it crosses the arm wall); then, turned back by +ANG about the
# vertical through the hinge, the share of its vertices exposed (rays up / down / 4 obliques must all hit the ship -> 0 %).
# Usage: blender -b <f.blend> --python lama_verifica_nacela.py -- <obj> <hx,hy,hz> <ANG>
import bpy, sys, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OBJ = a[0]; hx, hy, hz = (float(q) for q in a[1].split(",")); ANG = float(a[2])
bt = lambda o, M=None: BVHTree.FromPolygons([(M or o.matrix_world) @ v.co for v in o.data.vertices], [list(p.vertices) for p in o.data.polygons])
b = bpy.data.objects[OBJ]; Tb = bt(b)
for n in ("an_nacela_inchis_S", "an_nacela_deschis_S", "an_brat_fata_S"):
    ov = Tb.overlap(bt(bpy.data.objects[n])); print("VERIF deschisa x %-20s: %d perechi de triunghiuri care se taie" % (n, len(ov)))
ship = [o for o in bpy.data.collections["ASAMBLAT_NOU"].objects if not o.name.startswith(("an_lama", "lama")) and o.type == "MESH"]
V, F = [], []
for o in ship:
    k = len(V); V += [o.matrix_world @ v.co for v in o.data.vertices]; F += [[k + i for i in p.vertices] for p in o.data.polygons]
T = BVHTree.FromPolygons(V, F); P = Vector((hx - 1600, hy, hz)); M = Matrix.Translation(P) @ Matrix.Rotation(math.radians(ANG), 4, "Z") @ Matrix.Translation(-P)
dirs = [Vector(d).normalized() for d in ((0, 0, 1), (0, 0, -1), (1, 0, 1), (-1, 0, 1), (0, 1, -1), (0, -1, -1))]
pts = [M @ (b.matrix_world @ v.co) for v in b.data.vertices][::2]
e = sum(1 for q in pts if any(T.ray_cast(q + d * .3, d, 4000)[0] is None for d in dirs)); print("VERIF stransa (rotita %+.0f): %.1f%% varfuri expuse" % (ANG, 100 * e / len(pts)))
