# Bow diamond after the source gem: a shield outline (straight top edge, chamfered upper corners, a point
# below), standing proud of the nose with a flat central facet, facets sloping to the sides and a
# thickness fading toward the point. The lift field is blurred so every edge comes out rounded.
import bpy, bmesh, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body"
F = json.load(open(f"{D}/gems.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/body_v2.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in F]: bpy.data.objects.remove(o)
cb = bmesh.new(); cb.from_mesh(sc.objects["corp"].data); tree = BVHTree.FromBMesh(cb)
def signed_distance(O, X, Z):
    A = O[None, None]; B = np.roll(O, -1, 0)[None, None]; E = B - A; P = np.stack([X, Z], -1)[:, :, None]
    t = np.clip(((P - A) * E).sum(-1) / (E * E).sum(-1), 0, 1); d = np.linalg.norm(P - (A + E * t[..., None]), axis=-1).min(-1)
    a, b = A[..., 1], B[..., 1]; xi = (B[..., 0] - A[..., 0]) * (Z[..., None] - a) / np.where(b == a, 1e-9, b - a) + A[..., 0]
    inside = (((a > Z[..., None]) != (b > Z[..., None])) & (X[..., None] < xi)).sum(-1) % 2 == 1
    return np.where(inside, d, -d)
def blur(F2, sigma):
    k = np.exp(-0.5 * (np.arange(-int(3 * sigma), int(3 * sigma) + 1) / sigma) ** 2); k /= k.sum()
    F2 = np.apply_along_axis(lambda r: np.convolve(r, k, "same"), 1, F2)
    return np.apply_along_axis(lambda r: np.convolve(r, k, "same"), 0, F2)
for name, p in F.items():
    if name.startswith("_"): continue
    O = np.array(p["outline"], float); S = p.get("step", 1.0); M = p.get("margin", 10)
    xs = np.arange(O[:, 0].min() - M, O[:, 0].max() + M + S / 2, S); zs = np.arange(O[:, 1].min() - M, O[:, 1].max() + M + S / 2, S)
    X, Z = np.meshgrid(xs, zs); d = signed_distance(O, X, Z)
    zmin, zmax = O[:, 1].min(), O[:, 1].max(); v = np.clip((zmax - Z) / (zmax - zmin), 0, 1)
    row = np.where(d > 0, np.abs(X), 0).max(1, keepdims=True) + 1e-6           # half width of each row
    flat = p["flat"]; side = np.clip((np.abs(X) - flat) / np.maximum(row - flat, 1e-3), 0, 1)
    T = p["thick"] * (1 - p["taper"] * v) * (1 - p["facet"] * side * side * (3 - 2 * side))
    r = np.clip(d / p["rim"], 0, 1); shoulder = np.sin(r * np.pi / 2)            # the top edge: a short rounded wall
    top0 = np.clip(1 - (zmax - Z) / p["top_band"], 0, 1)
    ap = p["apron"] * (1 - 0.85 * top0)                                         # the slope shortens near the top so the deck line stays clean
    sl = np.clip((d + ap) / (ap + p["rim"]), 0, 1); slope = sl * sl * (3 - 2 * sl)  # sides and point: a long slope like C16
    top = np.clip(1 - (zmax - Z) / p["top_band"], 0, 1); top = top * top * (3 - 2 * top)
    prof = np.where(Z > zmax, shoulder, shoulder * top + slope * (1 - top))
    L = blur(T * prof, p["soften"])
    L = L - 0.8 * (1 - np.clip(L / 1.5, 0, 1))
    L = np.where(Z > zmax + 0.5, -0.8, L)                                       # a clean line where the deck meets the hull                                  # fades under the hull, no seam
    cz = p["centre_z"]; bm = bmesh.new(); G = {}
    for i in range(len(zs)):
        for j in range(len(xs)):
            if d[i, j] < -p["apron"] - 2: continue
            hit, nrm, _, _ = tree.ray_cast(Vector((xs[j], 2000, cz + zs[i])), Vector((0, -1, 0)), 3000)
            if hit is not None: dirn = (nrm + Vector((0, p.get("forward", 1.0), 0))).normalized(); G[(i, j)] = bm.verts.new(hit + dirn * float(L[i, j]))
    for (i, j) in list(G):
        q = [G.get((i, j)), G.get((i, j + 1)), G.get((i + 1, j + 1)), G.get((i + 1, j))]
        if None not in q: bm.faces.new(q)
    inner = [v for v in bm.verts if not v.is_boundary]
    for _ in range(p.get("relax", 0)): bmesh.ops.smooth_vert(bm, verts=inner, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    if p.get("deck_band"):
        # a horizontal deck on top for turrets: the upper band is pressed flat at the top edge's height
        deck_z = cz + zmax
        for (i, j), vv in G.items():
            a = np.clip((zs[i] - (zmax - p["deck_band"])) / p["deck_band"], 0, 1); a = a * a * (3 - 2 * a)
            a *= np.clip(L[i, j] / 2.0, 0, 1) * np.clip((d[i, j] + p["apron"]) / p["apron"], 0, 1)
            if vv.co.z < deck_z: vv.co.z += (deck_z - vv.co.z) * a
            else: vv.co.z += (deck_z - vv.co.z) * a
        for _ in range(3): bmesh.ops.smooth_vert(bm, verts=[v for v in inner if abs(v.co.z - deck_z) > 0.3], factor=0.4, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    nx = len(xs)
    for (i, j), vv in G.items():                                               # keep both halves identical
        m = G.get((i, nx - 1 - j))
        if m is not None and j < nx - 1 - j:
            a, b = vv.co.copy(), m.co.copy(); avg = Vector(((a.x - b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2))
            vv.co = avg; m.co = Vector((-avg.x, avg.y, avg.z))
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me)
    for pp in me.polygons: pp.use_smooth = True
    sc.collection.objects.link(bpy.data.objects.new(name, me))
bpy.data.libraries.write(f"{D}/body_v2.blend", {sc}, fake_user=True)
print("GEM ok")
