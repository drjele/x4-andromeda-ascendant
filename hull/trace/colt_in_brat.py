# A front arm's corner that pokes through a back arm pulled back inside it (asked: the outermost corner that goes into the
# arms, in on one side and out on the other - adjust it there a little): the vertices behind the PS (y < YMAX) that are outside
# the back arm and the PS are moved to the back arm's surface, IN m inside; their neighbours follow with a gaussian falloff
# (SIGMA m) so the surface stays smooth. Usage: blender -b <in> --python colt_in_brat.py -- <out> <front arm> <back arm> [YMAX IN SIGMA XIN]
import bpy, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import bmesh
a = sys.argv[sys.argv.index("--") + 1:]; OUT, NF, NB = a[0], a[1], a[2]; YMAX, IN, SIG, XIN = (float(q) for q in (a[3:7] if len(a) >= 7 else (-40, 1.0, 4.0, 100)))
def bvh(o): bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); return BVHTree.FromBMesh(bm), bm
f = bpy.data.objects[NF]; Tb, bmb = bvh(bpy.data.objects[NB]); Tp, bmp = bvh(bpy.data.objects["gp_PS"]); X0 = bpy.data.objects["gp_PS"].location.x
corner = lambda w: w.y < YMAX and abs(w.x - X0) < XIN                   # only the inner-side corner (nearer the ship's axis than XIN m)
def inside(T, p):                                                      # ray parity along +x
    n, q = 0, p.copy()
    while True:
        h = T.ray_cast(q, Vector((1, 0, 0)))
        if h[0] is None: return n % 2 == 1
        n += 1; q = h[0] + Vector((1e-3, 0, 0))
mw = f.matrix_world; inv = mw.inverted(); W = [mw @ v.co for v in f.data.vertices]
D = {}
for i, w in enumerate(W):
    if corner(w) and not inside(Tb, w) and not inside(Tp, w):
        loc, nrm, _, dist = Tb.find_nearest(w)
        if dist < 15: D[i] = (loc - nrm * IN) - w                              # onto the back arm, IN m inside
P = np.array([[w.x, w.y, w.z] for w in W]); ks = list(D); KP = P[ks]; KD = np.array([D[k][:] for k in ks])
moved = 0
for i, w in enumerate(W):
    if i in D: d = D[i]
    else:
        r = np.linalg.norm(KP - P[i], axis=1); j = int(np.argmin(r))
        if r[j] > 4 * SIG: continue
        d = Vector(KD[j] * np.exp(-r[j] ** 2 / (2 * SIG ** 2)))
    f.data.vertices[i].co = inv @ (w + d); moved += 1
f.data.update(); W2 = [f.matrix_world @ v.co for v in f.data.vertices]
left = sum(1 for i, w in enumerate(W2) if corner(w) and not inside(Tb, w) and not inside(Tp, w))
print("COLT %s: %d varfuri scoase din %s puse inapoi in el (max %.1f m), %d mutate cu vecinii; raman afara %d" % (
    NF, len(D), NB, max((d.length for d in D.values()), default=0), moved, left))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
