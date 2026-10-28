# The small V under the PS belly as its own component (asked: separate): a solid plate, outline from the reference (the
# lower plate of 169_C below the flat belly: tip at YT, half-width WR at y = 0), straight sides + a round tip of radius RT
# tangent to them, straight back with rounded corners; from just inside the belly (ZB + 1) down to ZJ, the bottom edge
# rounded (quarter circle of radius RR). Closed. Built in ship coordinates (x + DX), moved by OFF.
# Usage: blender -b <file.blend> --python ps_burta_v.py -- <out.blend> <dx> <off>
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, DX = a[0], float(a[1]); OFF = Vector([float(v) for v in a[2].split(",")])
env = lambda k, d: float(os.environ.get(k, d))
YT, WR, RT, ZB, ZJ, RR, RC = env("BV_VARF_Y", "276"), env("BV_LAT", "94"), env("BV_VARF_R", "25"), env("CORP_BURTA", "266"), env("BV_JOS", "246"), env("BV_RAZA", "6"), env("BV_COLT", "12")
cy = YT - RT; Pp, Cc = np.array([WR, 0.0]), np.array([0.0, cy]); d_ = np.linalg.norm(Cc - Pp); be = np.arcsin(RT / d_); u0 = (Cc - Pp) / d_
tx, ty = max([Pp + np.array([[np.cos(b), -np.sin(b)], [np.sin(b), np.cos(b)]]) @ u0 * np.sqrt(d_ ** 2 - RT ** 2) for b in (be, -be)], key=lambda p: p[0])
def outline(inset):                                                     # closed outline, counter-clockwise, offset inward
    pts = []
    ang0, ang1 = np.arctan2(ty - cy, tx), np.pi - np.arctan2(ty - cy, tx)
    for t in np.linspace(ang0, ang1, 60): pts.append((np.cos(t) * (RT - inset), cy + np.sin(t) * (RT - inset)))
    side = np.linspace(0, 1, 120)
    left = [(-(tx + (WR - tx) * f), ty * (1 - f)) for f in side]; right = [(WR - (WR - tx) * f, ty * f) for f in side]
    P = np.array(pts + left + [(x, 0.0) for x in np.linspace(-WR, WR, 80)] + right)
    k_ = np.exp(-0.5 * (np.arange(-8, 9) / (RC / 3)) ** 2); k_ /= k_.sum()   # rounded corners: the polygon smoothed around
    P = np.stack([np.convolve(np.r_[P[-8:, i], P[:, i], P[:8, i]], k_, "valid") for i in range(2)], 1)
    c = P.mean(0); return c + (P - c) * (1 - inset / max(WR, 1))     # inset as a uniform shrink toward the centre
if os.environ.get("BV_CONTUR"):                                         # the conical outlines from ps_burta_contur.py
    Ct = np.load(os.environ["BV_CONTUR"]); loops = list(zip(Ct["loops"], Ct["z"])); ZB, ZJ = float(Ct["z"][0]) - 1, float(Ct["z"][-1])
else: loops = [(outline(0.0), ZB + 1)] + [(outline(RR * (1 - np.cos(t))), ZJ + RR - RR * np.sin(t)) for t in np.linspace(0, np.pi / 2, 7)]
bm = bmesh.new(); rings = []
for P, z in loops: rings.append([bm.verts.new((x + DX, y, z)) for x, y in P])
n = len(rings[0])
for r0, r1 in zip(rings[:-1], rings[1:]):
    for i in range(n): bm.faces.new((r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]))
for r in (rings[0], rings[-1]):
    f = bm.faces.new(r if r is rings[-1] else r[::-1]); bmesh.ops.triangulate(bm, faces=[f])
for _ in range(6):
    long_ = [e for e in bm.edges if e.calc_length() > 6.0 and all(abs(v.co.z - (ZB + 1)) < 1e-3 or abs(v.co.z - ZJ) < 1e-3 for v in e.verts)]
    if not long_: break
    bmesh.ops.subdivide_edges(bm, edges=long_, cuts=1, use_grid_fill=False); bmesh.ops.triangulate(bm, faces=bm.faces[:])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new(os.environ.get("NUME_PREFIX", "comp_") + "burta_V"); bm.to_mesh(me); bm.free()
src = bpy.data.objects["R002 169_C"]; me.materials.append(src.material_slots[src.data.polygons[0].material_index].material)
for p in me.polygons: p.use_smooth = True
col = bpy.data.collections.get(os.environ.get("COLECTIE", "PS_NOU_EXPLODAT"))
if os.environ.get("NUME_PREFIX", "comp_") + "burta_V" in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[os.environ.get("NUME_PREFIX", "comp_") + "burta_V"])
o = bpy.data.objects.new(os.environ.get("NUME_PREFIX", "comp_") + "burta_V", me); col.objects.link(o); o.location = OFF
print("BURTA V: varf y %.0f (raza %.0f), lata %.0f m la y 0, de la z %.0f la %.0f, muchia de jos raza %.0f; %d varfuri" % (YT, RT, 2 * WR, ZB + 1, ZJ, RR, len(me.vertices)))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
