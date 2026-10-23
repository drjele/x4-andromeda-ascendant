# Teardrop fairings lying on the superellipse body; both sides; edges sunk into the body.
import bpy, bmesh, json, math, sys
import numpy as np
from mathutils import Vector
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body"
G = json.load(open(f"{D}/body_grid.json")); BS = json.load(open(f"{D}/body_super.json")); TOP_SCALE, TOP_N = BS.get("top_scale", 1.0), BS.get("top_n", 2.0); F = json.load(open(f"{D}/fairings.json"))
gy = np.array(G["y"])
def sec(y):
    return [float(np.interp(y, gy, G[k])) for k in ("a", "b", "zc", "n")]
def top_half(y):
    return float(np.interp(y, gy, G["bt"]))
def surf(y, th):
    a, b, zc, n = sec(y); c, s = math.cos(th), math.sin(th)
    if s > 0: b, n = top_half(y), TOP_N
    x = a * math.copysign(abs(c) ** (2 / n), c); z = zc + b * math.copysign(abs(s) ** (2 / n), s)
    # normal of |x/a|^n + |z/b|^n = 1
    nx = math.copysign(abs(x / a) ** (n - 1), x) / a if a > 1e-6 else 0
    nz = math.copysign(abs((z - zc) / b) ** (n - 1), z - zc) / b if b > 1e-6 else 0
    nv = Vector((nx, 0, nz)).normalized() if (nx or nz) else Vector((0, 0, 1))
    return Vector((x, y, z)), nv
SINK = 3.0; NA, NY = 24, 120
def fairing(bm, p, side):
    y0, y1 = p["y"]; ts = p["t"]
    # each profile: linear through the stations, then a wide gaussian along the part, so it flows
    # as one curve (no plateaus or necks between stations); the ends keep their own values
    TT = np.linspace(0, 1, 401); SIG = p.get("smooth", 0.05)
    def _prof(v):
        lin = np.interp(TT, ts, v); r = int(3 * SIG * 400); k = np.exp(-0.5 * (np.arange(-r, r + 1) / (SIG * 400)) ** 2); k /= k.sum()
        sm = np.convolve(np.pad(lin, r, mode="reflect", reflect_type="odd"), k, "valid")
        return sm
    PROF = {k: _prof(p[k]) for k in ("angle", "height", "half", "half_m") if k in p}
    def val(key, t):
        return float(np.interp(t, TT, PROF[key]))
    rows = []
    for j in range(NY + 1):
        t = j / NY; y = y0 + (y1 - y0) * t
        th0 = math.radians(val("angle", t)); height = val("height", t)
        if "half_m" in p:
            a, b, zc, n = sec(y); half = val("half_m", t) / max(5.0, 0.5 * (a + b))
        else:
            half = math.radians(val("half", t))
        row = []
        for i in range(NA + 1):
            u = -1 + 2 * i / NA
            pt, nv = surf(y, th0 + u * half)
            dome = max(0.0, 1 - u * u) ** 0.6
            q = pt + nv * (height * dome - SINK * (1 - dome))
            row.append(Vector((q.x * side, q.y, q.z)))
        rows.append([bm.verts.new(v) for v in row])
    for a, b in zip(rows, rows[1:]):
        for i in range(NA):
            bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]) if side > 0 else (a[i], b[i], b[i + 1], a[i + 1]))
    # close both ends so no open edge shows
    for ring in (rows[0], rows[-1]):
        c = bm.verts.new(sum((v.co for v in ring), Vector()) / len(ring))
        for i in range(NA):
            bm.faces.new((ring[i], ring[i + 1], c))


bpy.ops.wm.open_mainfile(filepath=f"{D}/body.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in F]: bpy.data.objects.remove(o)
for name, p in F.items():
    if name.startswith("_"): continue
    bm = bmesh.new()
    for side in ((1,) if p.get("centre") else (1, -1)): fairing(bm, p, side)
    bm.normal_update()
    # outward check on the right half
    bm.faces.ensure_lookup_table(); f = bm.faces[len(bm.faces) // 4]
    yv = f.calc_center_median().y; a, b, zc, n = sec(yv)
    if f.normal.dot(f.calc_center_median() - Vector((0, yv, zc))) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me)
    for pp in me.polygons: pp.use_smooth = True
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
bpy.data.libraries.write(f"{D}/body_v2.blend", {sc}, fake_user=True)
print("FAIRINGS ok")
