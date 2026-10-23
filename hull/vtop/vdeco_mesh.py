# V decorations: ridges on the plate top (projected from above) and the keel under the plate.
import bpy, bmesh, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/vtop"
F = json.load(open(f"{D}/vdeco.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/v_scene.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in F]: bpy.data.objects.remove(o)
bv = bmesh.new(); bv.from_mesh(sc.objects["v_plate"].data); tree = BVHTree.FromBMesh(bv)
def prof(lst, t, sig=0.08):
    TT = np.linspace(0, 1, 401); lin = np.interp(TT, np.linspace(0, 1, len(lst)), lst)
    r = int(3 * sig * 400); k = np.exp(-0.5 * (np.arange(-r, r + 1) / (sig * 400)) ** 2); k /= k.sum()
    return max(float(np.interp(t, TT, np.convolve(np.pad(lin, r, mode="reflect", reflect_type="odd"), k, "valid"))), 0.0)
def curve(pts):
    P = [pts[0]] + pts + [pts[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = map(np.array, P[i - 1:i + 3]); n = max(2, int(np.linalg.norm(p2 - p1) / 2))
        for k in range(n):
            t = k / n; out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
    return out + [np.array(pts[-1])]
NU = 14
def ridge(bm, p, side):
    rows = []; path = []
    for q in curve(p["points"]):
        h = tree.ray_cast(Vector((q[0] * side, q[1], 2000)), Vector((0, 0, -1)), 4000)
        if h[0] is not None: path.append((h[0], h[1]))
    N = len(path)
    for i, (pt, n) in enumerate(path):
        t = i / (N - 1); tan = (path[min(i + 1, N - 1)][0] - path[max(i - 1, 0)][0]).normalized(); sv = tan.cross(Vector((0, 0, 1))).normalized()
        w, h = prof(p["half"], t), prof(p["height"], t); row = []
        for j in range(NU + 1):
            u = -1 + 2 * j / NU; q = pt + sv * u * w
            hit = tree.ray_cast(q + Vector((0, 0, 200)), Vector((0, 0, -1)), 400)[0] or q
            row.append(bm.verts.new(hit + Vector((0, 0, h * (1 - u * u) ** 1.5 - 1.0 * u ** 8))))
        rows.append(row)
    for a, b in zip(rows, rows[1:]):
        for j in range(NU): bm.faces.new((a[j], a[j + 1], b[j + 1], b[j]))
for name, p in F.items():
    if name.startswith("_"): continue
    bm = bmesh.new()
    if name == "v_keel":
        k = np.load(f"{D}/vkeel.npz"); kx, ky, km, kd, ku = k["xs"], k["ys"], k["mask"], k["depth"], k["under"]; G = {}
        for i in range(len(ky)):
            for j in range(len(kx)):
                if km[i, j]: G[(i, j)] = bm.verts.new((kx[j], ky[i], ku[i, j] + 0.5 - kd[i, j]))
        for (i, j) in list(G):
            q = [G.get((i, j)), G.get((i + 1, j)), G.get((i + 1, j + 1)), G.get((i, j + 1))]
            if None not in q: bm.faces.new(q)
        edge = [v for v in bm.verts if v.is_boundary]
        for _ in range(10): bmesh.ops.smooth_vert(bm, verts=edge, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=False)
    else:
        for s in (1, -1): ridge(bm, p, s)
        free = [v for v in bm.verts if not v.is_boundary]
        for _ in range(4): bmesh.ops.smooth_vert(bm, verts=free, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me)
    for pp in me.polygons: pp.use_smooth = True
    sc.collection.objects.link(bpy.data.objects.new(name, me))
bpy.data.libraries.write(f"{D}/v_scene.blend", {sc}, fake_user=True)
print("VDECO ok")
