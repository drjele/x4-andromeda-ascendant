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
def interp(lst, t):
    if len(lst) == 1: return lst[0]
    x = t * (len(lst) - 1); i = min(int(x), len(lst) - 2); f = x - i
    return lst[i] + (lst[i + 1] - lst[i]) * f
def dense(p):
    if "circle" in p:
        cx, cz, r = p["circle"]
        return [(cx + r * math.cos(2 * math.pi * k / 72), cz + r * math.sin(2 * math.pi * k / 72)) for k in range(72)]
    pts = p["points"]; out = []
    for (a0, b0), (a1, b1) in zip(pts, pts[1:]):
        n = max(2, int(math.hypot(a1 - a0, b1 - b0) / 3))
        out += [(a0 + (a1 - a0) * k / n, b0 + (b1 - b0) * k / n) for k in range(n)]
    return out + [tuple(pts[-1])]
def build(bm, p, side):
    path = []
    for a, b in dense(p):
        if p["view"] == "side": hit, n = project("side", a, b)
        else: hit, n = project(p["view"], a * side, b)
        if hit: path.append((hit, n))
    closed = p.get("closed", False); N = len(path)
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
