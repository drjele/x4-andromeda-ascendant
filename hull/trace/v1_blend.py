# V1 (the V plate) blended into the arm roots A10: the roots end in a wall at |x| ~ 100 standing up to 17 m above the
# plate's edge toward the back (a step and a slit seen from above), and toward the front the two surfaces cross back
# and forth (a jagged seam). The plate's top skin rises gradually from |x| = x0 to the root's height at the seam and
# stays just under the root beyond it, so the two meet flush; the underside is left as it is.
# Usage: blender -b --python v1_blend.py
import bpy, bmesh, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"; K = json.load(open(f"{D}/trace/v1_blend.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]
def tree(n):
    o = sc.objects[n]; b = bmesh.new(); b.from_mesh(o.data); b.transform(o.matrix_world); return BVHTree.FromBMesh(b)
def top(t, x, y):
    h = t.ray_cast(Vector((x, y, 3000)), Vector((0, 0, -1)))[0]; return h.z if h is not None else None
# the plate's rear corner at the seam is pulled back until it meets the end of the root (a wedge stayed open there)
C = K["corner"]; o = sc.objects["v_plate"]; M = o.matrix_world; Mi = M.inverted(); moved = 0
for vt in o.data.vertices:
    p = M @ vt.co; d = ((abs(p.x) - K["seam"]) ** 2 + (p.y - C["y"]) ** 2) ** 0.5
    if p.y < C["y"] + C["front"] and d < C["radius"]:
        u = 1 - d / C["radius"]; vt.co = Mi @ (p + Vector((0, C["dy"] * u * u * (3 - 2 * u), 0))); moved += 1
o.data.update()
V, R = tree("v_plate"), tree("arm_root_r")
# the step at the seam, per y: the root's top just outboard of its wall against the plate's top at the wall
gy = np.arange(-260, 460, 5.0); step = np.zeros(len(gy)); xs = K["seam"]
for i, y in enumerate(gy):
    r, v = top(R, xs + K["probe"], y), top(V, xs, y)
    if r is not None and v is not None: step[i] = r + K["above"] - v
k = np.exp(-0.5 * (np.arange(-6, 7) / 2.0) ** 2); step = np.convolve(np.pad(step, 6, mode="edge"), k / k.sum(), "valid")
n = 0; mx = 0.0
for vt in o.data.vertices:
    p = M @ vt.co; ax = abs(p.x)
    if ax < K["x0"]: continue
    vz = top(V, p.x, p.y)
    if vz is None or p.z < vz - K["skin"]: continue                         # the top skin only
    u = min(1.0, (ax - K["x0"]) / (xs - K["x0"])); w = u * u * (3 - 2 * u)
    dz = w * float(np.interp(p.y, gy, step))
    if ax > xs:                                                            # past the wall: stay under the root
        r = top(R, abs(p.x), p.y)
        if r is not None: dz = min(dz, r - K["under"] - p.z)
    if dz > 0: vt.co = Mi @ (p + Vector((0, 0, dz))); n += 1; mx = max(mx, dz)
o.data.update(); bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("V1 BLEND corner %d moved, %d vertices raised, up to %.0f m" % (moved, n, mx))
