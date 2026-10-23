import bpy, bmesh, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body"
F = json.load(open(f"{D}/paths.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/body_v2.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in F]: bpy.data.objects.remove(o)
bb = bmesh.new(); bb.from_mesh(sc.objects["corp"].data); tree = BVHTree.FromBMesh(bb)
SINK = 1.5; NU = 20
def project(view, a, b):
    if view == "below": o, d = Vector((a, b, -3000)), Vector((0, 0, 1))
    elif view == "above": o, d = Vector((a, b, 3000)), Vector((0, 0, -1))
    elif view == "behind": o, d = Vector((a, -3000, b)), Vector((0, 1, 0))
    else: o, d = Vector((3000, a, b)), Vector((-1, 0, 0))
    hit, n, _, _ = tree.ray_cast(o, d, 6000); return hit, n
_PROF = {}
def interp(lst, t, sig=0.06):
    if len(lst) == 1: return lst[0]
    key = tuple(lst)
    if key not in _PROF:
        TT = [i / 400 for i in range(401)]; xs = [i / (len(lst) - 1) for i in range(len(lst))]
        import numpy as _np
        lin = _np.interp(TT, xs, lst); r = int(3 * sig * 400); k = _np.exp(-0.5 * (_np.arange(-r, r + 1) / (sig * 400)) ** 2); k /= k.sum()
        _PROF[key] = _np.convolve(_np.pad(lin, r, mode="reflect", reflect_type="odd"), k, "valid")
    import numpy as _np
    return max(float(_np.interp(t, _np.linspace(0, 1, 401), _PROF[key])), 0.0)
def dense(p):
    if "circle" in p:
        cx, cz, r = p["circle"]
        return [(cx + r * math.cos(2 * math.pi * k / 96), cz + r * math.sin(2 * math.pi * k / 96)) for k in range(96)]
    pts = [tuple(q) for q in p["points"]]
    # Catmull-Rom through the points, sampled about every 2 m
    P_ = [pts[0]] + pts + [pts[-1]]; out = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        n = max(2, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / 2))
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * (2 * p1[c] + (p2[c] - p0[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t * t + (3 * p1[c] - p0[c] - 3 * p2[c] + p3[c]) * t ** 3) for c in (0, 1)))
    return out + [pts[-1]]

def build(bm, p, side):
    path = []
    for a, b in dense(p):
        if p["view"] == "side": hit, n = project("side", a, b)
        else: hit, n = project(p["view"], a * side, b)
        if hit: path.append((hit, n))
    closed = p.get("closed", False); N = len(path)
    win = 4
    path = [(path[i][0], sum((path[(i + k) % N if closed else min(max(i + k, 0), N - 1)][1] for k in range(-win, win + 1)), Vector()).normalized()) for i in range(N)]
    rows = []
    for i, (pt, n) in enumerate(path):
        t = i / (N - 1 if not closed else N)
        tan = (path[(i + 1) % N][0] - path[i - 1][0]) if closed else (path[min(i + 1, N - 1)][0] - path[max(i - 1, 0)][0])
        sv = tan.normalized().cross(n).normalized()
        w, h = interp(p["half"], t), interp(p["height"], t)
        insign = 0
        if "inner_flat" in p:
            ix, iy = p["inner_flat"]
            insign = 1 if sv.dot(Vector((ix, iy, pt.z)) - pt) > 0 else -1
        row = []
        for j in range(NU + 1):
            u = -1 + 2 * j / NU
            s_ = u * insign
            ww = w
            if insign and s_ > 0:
                # the inner side cannot reach past the centre of the bend, or it folds over itself
                a_ = path[max(i - 6, 0)][0]; b_ = path[min(i + 6, N - 1)][0]
                chord = (b_ - a_).length; t1 = (pt - a_).normalized(); t2 = (b_ - pt).normalized()
                ang = math.acos(max(-1.0, min(1.0, t1.dot(t2))))
                radius = chord / (2 * math.sin(ang / 2)) if ang > 1e-3 else 1e9
                ww = min(w, 0.75 * radius)
            q = pt + sv * u * ww
            hit, hn = tree.find_nearest(q)[:2]
            if insign and s_ > 0:
                # inner half: a flat top, then a steep flat wall down to the hull
                k = min(1.0, max(0.0, (s_ - 0.8) / 0.2))
                lift = h * (1 - k) - SINK * k
            else:
                lift = h * (1 - u * u) ** 1.5 - SINK * u ** 8
            row.append(bm.verts.new(hit + hn * lift))
        rows.append(row)
    pairs = list(zip(rows, rows[1:])) + ([(rows[-1], rows[0])] if closed else [])
    for a, b in pairs:
        for j in range(NU): bm.faces.new((a[j], a[j + 1], b[j + 1], b[j]))
for name, p in F.items():
    if name.startswith("_"): continue
    if p.get("through_axis"):
        # one continuous path from the left tip through the axis to the right tip
        pts = p["points"]; p = dict(p)
        p["points"] = [[-a, b] for a, b in reversed(pts[1:])] + pts
        p["half"] = list(reversed(p["half"][1:])) + p["half"]; p["height"] = list(reversed(p["height"][1:])) + p["height"]
        p["centre"] = True
    bm = bmesh.new()
    sides = (1,) if p.get("centre") else (1, -1)
    if p["view"] == "side":
        build(bm, p, 1); bm2 = bmesh.new()
    else:
        for s in sides: build(bm, p, s)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.05)
    if not p.get("sharp"):
        free = [v for v in bm.verts if not v.is_boundary]
        for _ in range(p.get("relax", 4)):
            bmesh.ops.smooth_vert(bm, verts=free, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me)
    if p["view"] == "side":
        # mirror the side part to the left
        b3 = bmesh.new(); b3.from_mesh(me)
        bmesh.ops.mirror(b3, geom=b3.verts[:] + b3.edges[:] + b3.faces[:], axis="X", merge_dist=0.01)
        bmesh.ops.recalc_face_normals(b3, faces=b3.faces[:]); b3.to_mesh(me)
    for pp in me.polygons: pp.use_smooth = True
    sc.collection.objects.link(bpy.data.objects.new(name, me))
bpy.data.libraries.write(f"{D}/body_v2.blend", {sc}, fake_user=True)
print("PATHS ok")
