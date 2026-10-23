# Wing decorations on the top of each link, from the source: the eye (a teardrop frame pointing outboard
# with a dome inside) and the long rib sweeping forward to the arm. Each is a smooth relief lifted along
# the link's normal over a top-view outline, mirrored to the left link.
import bpy, bmesh, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
F = json.load(open(f"{D}/links/wdeco.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]
names = [n + s for n in F for s in ("_r", "_l")]
for o in [o for o in sc.objects if o.name in names]: bpy.data.objects.remove(o)
b = bmesh.new(); b.from_mesh(sc.objects["link_r"].data); T = BVHTree.FromBMesh(b)
def rounded(outline, n=160, r=0.4):
    P = np.array(outline, float); P = np.vstack([P, P[:1]]); seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    s = np.linspace(0, seg[-1], n, endpoint=False); Q = np.stack([np.interp(s, seg, P[:, c]) for c in (0, 1)], 1)
    sig = max(r * n / len(outline) / 2, 0.5); k = np.exp(-0.5 * (np.arange(-int(3 * sig), int(3 * sig) + 1) / sig) ** 2); k /= k.sum(); m = len(k) // 2
    return np.stack([np.convolve(np.r_[Q[-m:, c], Q[:, c], Q[:m, c]], k, "valid") for c in (0, 1)], 1)
def sdist(O, X, Y):
    A = O[None, None]; B = np.roll(O, -1, 0)[None, None]; E = B - A; P = np.stack([X, Y], -1)[:, :, None]
    t = np.clip(((P - A) * E).sum(-1) / (E * E).sum(-1), 0, 1); d = np.linalg.norm(P - (A + E * t[..., None]), axis=-1).min(-1)
    a, b2 = A[..., 1], B[..., 1]; xi = (B[..., 0] - A[..., 0]) * (Y[..., None] - a) / np.where(b2 == a, 1e-9, b2 - a) + A[..., 0]
    ins = (((a > Y[..., None]) != (b2 > Y[..., None])) & (X[..., None] < xi)).sum(-1) % 2 == 1
    return np.where(ins, d, -d)
def along(v, sig):
    k = np.exp(-0.5 * (np.arange(-int(3 * sig), int(3 * sig) + 1) / sig) ** 2); k /= k.sum(); m = len(k) // 2
    return np.convolve(np.r_[np.full(m, v[0]), v, np.full(m, v[-1])], k, "valid")
def path_field(p, X, Y):
    P = np.array(p["path"], float); W = np.array(p["width"], float); H = np.array(p["height"], float)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; ss = np.linspace(0, s[-1], 200)
    # the path and its width and height are smoothed along the rib, so the control points leave no kinks
    C = np.stack([along(np.interp(ss, s, P[:, c]), p["smooth"]) for c in (0, 1)], 1); w = along(np.interp(ss, s, W), p["smooth"]); h = along(np.interp(ss, s, H), p["smooth"])
    Q = np.stack([X, Y], -1)[..., None, :]; dd = np.linalg.norm(Q - C, axis=-1); i = dd.argmin(-1); dm = dd.min(-1)
    # a flat deck across the middle of the rib, then a long soft slope onto the wing
    r = dm / (w[i] / 2); s = np.clip((1 + p["apron"] / (w[i] / 2) - r) / (1 + p["apron"] / (w[i] / 2) - p["flat"]), 0, 1)
    return h[i] * s * s * (3 - 2 * s)
for name, p in F.items():
    pts = np.array(p.get("outline", p.get("path")), float); M = 30
    xs = np.arange(pts[:, 0].min() - M, pts[:, 0].max() + M, 1.0); ys = np.arange(pts[:, 1].min() - M, pts[:, 1].max() + M, 1.0)
    X, Y = np.meshgrid(xs, ys)
    if p["kind"] == "rib": L = path_field(p, X, Y)
    else:
        O = rounded(p["outline"], r=p["round"]); d = sdist(O, X, Y)
        if p["kind"] == "ring":
            u = np.clip(1 - np.abs(d) / (p["width"] / 2), 0, 1); L = p["height"] * np.sin(u * np.pi / 2)
        else:
            # a flat top, then a long soft slope out onto the wing as on the crescent
            s = np.clip((d + p["apron"]) / (p["apron"] + p["rim"]), 0, 1); L = p["height"] * s * s * (3 - 2 * s)
            DOME = None
            if "dome" in p:
                # a round cap that lands on the plate with a short tangent foot instead of a crease
                q = p["dome"]; d2 = sdist(rounded(q["outline"], r=q["round"]), X, Y); u2 = np.clip(d2 / q["rim"], 0, 1); f = np.clip(u2 / q["foot"], 0, 1)
                DOME = q["height"] * np.sqrt(1 - (1 - u2) ** 2) * f * f * (3 - 2 * f)
    if p["kind"] == "rib": DOME = None
    L = np.where(L > 0, L + 0.3, -3.0)                               # a hair above the wing skin, then straight under it
    bm = bmesh.new(); G = {}
    for i in range(len(ys)):
        for j in range(len(xs)):
            if L[i, j] < 0 and not any(0 <= i + a < len(ys) and 0 <= j + c < len(xs) and L[i + a, j + c] > 0 for a in (-1, 0, 1) for c in (-1, 0, 1)): continue
            hit, nrm, _, _ = T.ray_cast(Vector((xs[j], ys[i], 400)), Vector((0, 0, -1)), 900)
            if hit is not None: G[(i, j)] = bm.verts.new(hit + nrm * float(L[i, j]))
    if p.get("flat") is True:
        # the top of the plate is pressed onto one plane so an L turret sits level on it
        top = [(k, v) for k, v in G.items() if L[k] > p["height"] - 0.05]
        A = np.array([[v.co.x, v.co.y, 1.0] for _, v in top]); zc = np.linalg.lstsq(A, np.array([v.co.z for _, v in top]), rcond=None)[0]
        nrm_p = Vector((-zc[0], -zc[1], 1)).normalized()
        for k, v in G.items():
            w = np.clip(L[k] / p["height"], 0, 1) ** 3; zp = zc[0] * v.co.x + zc[1] * v.co.y + zc[2]
            v.co.z = v.co.z + (zp - v.co.z) * w
            if DOME is not None and DOME[k] > 0: v.co = v.co + nrm_p * float(DOME[k])
    for (i, j) in list(G):
        q = [G.get((i, j)), G.get((i, j + 1)), G.get((i + 1, j + 1)), G.get((i + 1, j))]
        if None not in q: bm.faces.new(q)
    for _ in range(3): bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if not v.is_boundary], factor=0.4, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY"); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name + "_r"); bm.to_mesh(me)
    for pp in me.polygons: pp.use_smooth = True
    sc.collection.objects.link(bpy.data.objects.new(name + "_r", me))
    ml = me.copy(); ml.name = name + "_l"; ml.transform(Matrix.Scale(-1, 4, (1, 0, 0))); ml.flip_normals()
    sc.collection.objects.link(bpy.data.objects.new(name + "_l", ml))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("WDECO ok")
