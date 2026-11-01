# Mounts the confirmed R109 shark-fin surface (sup_fin_A, built beside its guides by SUP=1 ghidaj_fin2.py) on the ship as
# an_R109_S / an_R109_D (asked: smooth it, then mount it in the right place). Axis seen from above = the ear/PS junction line
# x = K*y + B, the fin's front tip (local y = L) at ship y = SF, its length running back along the line. The flat base = the plane
# fitted (least squares) to the surface under the base outline (rays from above onto ear + PS + PS frame), lowered until the whole
# base lies at or under that surface (+ SINK m), so it never floats; the fin stands along that plane's normal.
# Local frame of sup_fin_A: x = across (minus its x0), y = along (front +y), z = up, base at z = 0.
# Ship coords = world + X0 on x (ASAMBLAT_NOU pieces have location x -X0, mesh in ship coords). D = mirror x -> -x, faces reversed.
# Usage: blender -b <scene.blend> --python monteaza_fin.py -- <out.blend> [x0=1600] [guide x0=-5200]
#        env K=0.173 B=-140.1 SF=167 SINK=0.2
import bpy, sys, os, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; X0 = float(a[1]) if len(a) > 1 else 1600.0; GX = float(a[2]) if len(a) > 2 else -5200.0
E = lambda k, d: float(os.environ.get(k, d))
K, B, SF, SINK = E("K", .173), E("B", -140.1), E("SF", 167), E("SINK", .2)
V, F = [], []
for n in ("an_ureche_S", "an_PS", "an_PS_rama"):
    o = bpy.data.objects[n]; b = len(V); V += [tuple(o.matrix_world @ v.co + Vector((X0, 0, 0))) for v in o.data.vertices]
    F += [[b + i for i in p.vertices] for p in o.data.polygons]
bvh = BVHTree.FromPolygons([Vector(p) for p in V], F)
def zs(x, y):
    h = bvh.ray_cast(Vector((x, y, 2000.0)), Vector((0, 0, -1)))
    if h[0] is None: raise SystemExit("ray miss %.1f %.1f" % (x, y))
    return h[0].z
src = bpy.data.objects["sup_fin_A"]; P = np.array([v.co[:] for v in src.data.vertices]); P[:, 0] -= GX
Fs = [list(p.vertices) for p in src.data.polygons]
L = P[:, 1].max()
d = np.array([K, 1.0]); d /= np.linalg.norm(d); nrm = np.array([d[1], -d[0]])
O2 = np.array([K * SF + B, SF]) - d * L                                  # ship xy of local (0, 0)
xy = lambda lx, ly: O2 + d * ly + nrm * lx
bs = P[np.abs(P[:, 2]) < 1e-3]                                          # base vertices (z = 0): the footprint
bs = bs[::max(1, len(bs) // 1500)]
Z = np.array([zs(*xy(x, y)) for x, y, _ in bs])
A = np.c_[np.ones(len(bs)), bs[:, 1], bs[:, 0]]; c = np.linalg.lstsq(A, Z, rcond=None)[0]   # z = c0 + c1*ly + c2*lx
res = Z - A @ c; off = -res.min() + SINK                                 # lower the plane under every surface point (+ SINK)
ey = np.array([d[0], d[1], c[1]]); ey /= np.linalg.norm(ey)
ex = np.array([nrm[0], nrm[1], c[2]]); ex -= ey * (ex @ ey); ex /= np.linalg.norm(ex)
ez = np.cross(ex, ey)
if ez[2] < 0: ez = -ez
O = np.array([O2[0], O2[1], c[0] - off])
Q = O + np.outer(P[:, 0], ex) + np.outer(P[:, 1], ey) + np.outer(P[:, 2], ez)
for nm, VV, FF in (("an_R109_S", Q, Fs), ("an_R109_D", Q * [-1, 1, 1], [f[::-1] for f in Fs])):
    o = bpy.data.objects[nm]; old = o.data; me = bpy.data.meshes.new(nm); me.from_pydata([tuple(v) for v in VV], [], FF)
    for p in me.polygons: p.use_smooth = True
    sharp = src.data.attributes.get("sharp_edge")
    if sharp:                                                          # keep the base / back face margins hard
        key = {tuple(sorted(e.vertices)): sharp.data[i].value for i, e in enumerate(src.data.edges)}
        at = me.attributes.new("sharp_edge", "BOOLEAN", "EDGE")
        for i, e in enumerate(me.edges): at.data[i].value = key.get(tuple(sorted(e.vertices)), False)
    for m in old.materials: me.materials.append(m)
    o.data = me; o.location = (-X0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
    if old.users == 0: bpy.data.meshes.remove(old)
tilt = np.degrees(np.arccos(ez[2]))
print("MONTAT: varf fata la y %.1f, spate (y local 0) la y %.1f; plan baza inclinat %.1f grade fata de orizontala; suprafata sub baza "
      "variaza %.2f m fata de plan; baza coborata %.2f m sub plan (cel mai adanc punct al bazei %.2f m sub suprafata)"
      % (SF, O2[1], tilt, res.max() - res.min(), off, res.max() + off))
print("BAZA: colturi spate S", tuple(np.round(Q[np.argmin(P[:, 1] - 34 + np.abs(P[:, 0] + 15) + np.abs(P[:, 2]))], 1)))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
