# Parts lifted from a measured source-minus-body height field (right half, mirrored).
import bpy, bmesh, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body"
F = json.load(open(f"{D}/heightparts.json"))
SINK = 1.5

def blur(a, s):
    r = int(3 * s) + 1; k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2); k /= k.sum()
    a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, r, mode="edge"), k, "valid"), 0, a)
    return np.apply_along_axis(lambda v: np.convolve(np.pad(v, r, mode="edge"), k, "valid"), 1, a)

def largest(mask):
    seen = np.zeros_like(mask); best = []
    for start in zip(*np.nonzero(mask)):
        if seen[start]: continue
        stack, comp = [start], []; seen[start] = True
        while stack:
            i, j = stack.pop(); comp.append((i, j))
            for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                if 0 <= a < mask.shape[0] and 0 <= b < mask.shape[1] and mask[a, b] and not seen[a, b]:
                    seen[a, b] = True; stack.append((a, b))
        if len(comp) > len(best): best = comp
    out = np.zeros_like(mask)
    for i, j in best: out[i, j] = True
    return out

def grow(mask, n):
    m = mask.copy()
    for _ in range(n):
        g = m.copy(); g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]; m = g
    return m

bpy.ops.wm.open_mainfile(filepath=f"{D}/body_v2.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in F]: bpy.data.objects.remove(o)
bb = bmesh.new(); bb.from_mesh(sc.objects["corp"].data); tree = BVHTree.FromBMesh(bb)
def field_part(p):
    f = np.load(f"{D}/{p['field']}"); xs, ys, dz = f["xs"], f["ys"], np.nan_to_num(f["dz"], nan=-99)
    cols = np.nonzero((xs >= p["x"][0]) & (xs <= p["x"][1]))[0]; rows = np.nonzero((ys >= p["y"][0]) & (ys <= p["y"][1]))[0]
    xs, ys, dz = xs[cols], ys[rows], dz[np.ix_(rows, cols)]
    keep = largest(dz > p["min"])
    # a smooth outline (blurred mask) and a smooth top; the lift fades to zero at the outline
    soft = blur(keep.astype(float), p["smooth"] * 2)
    top = blur(np.where(keep, np.minimum(dz, p["cap"]), 0.0), p["smooth"]) / np.maximum(blur(keep.astype(float), p["smooth"]), 0.3)
    edge = np.clip((soft - 0.25) / 0.35, 0, 1); edge = edge * edge * (3 - 2 * edge)
    # fade out toward the outer limit of the window too
    fx = np.clip((p["x"][1] - xs) / p.get("fade", 20.0), 0, 1); edge = edge * (fx * fx * (3 - 2 * fx))[None, :]
    h = np.minimum(top, p["cap"]) * edge
    region = grow(soft > 0.2, 2)
    if "scale_y" in p:
        (ya, fa), (yb, fb) = p["scale_y"]
        t = np.clip((ys - ya) / (yb - ya), 0, 1); t = t * t * (3 - 2 * t)
        wy = (1 - t)[:, None]
        xa, xb = p.get("scale_x", [1e9, 1e9])
        u = np.clip((xs - xa) / (xb - xa), 0, 1); wx = (1 - u * u * (3 - 2 * u))[None, :]
        # extra height on the rear middle only, blurred wide so it slopes down gradually into the hull
        extra = blur(h * (fa - 1) * wy * wx, p.get("ramp", 4))
        h = h + extra
        region = region | grow(extra > 0.3, 1)

    return xs, ys, h, region

BAND_INSIDE = [None]

def band_field(p):
    # distance from each grid point to the centreline (both halves through the axis), its position along it
    pts = np.array(p["points"], float); full = np.vstack([pts[::-1] * [-1, 1], pts[1:]])
    halves = np.r_[p["half"][::-1], p["half"][1:]]; heights = np.r_[p["height"][::-1], p["height"][1:]]
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(full, axis=0), axis=1))]; T = seg / seg[-1]
    dense_t = np.linspace(0, 1, 800); line = np.stack([np.interp(dense_t, T, full[:, k]) for k in (0, 1)], 1)
    hw = np.interp(dense_t, T, halves); hh = np.interp(dense_t, T, heights)
    # smooth the width and height profiles along the band so they change without kinks
    ker = np.exp(-0.5 * (np.arange(-60, 61) / 20.0) ** 2); ker /= ker.sum()
    hw = np.convolve(np.pad(hw, 60, mode="edge"), ker, "valid"); hh = np.convolve(np.pad(hh, 60, mode="edge"), ker, "valid")
    S = p["step"]; R = p.get("outer", 1.0) * halves.max() + 6
    xs = np.arange(0, line[:, 0].max() + R, S); ys = np.arange(line[:, 1].min() - R, line[:, 1].max() + R, S)
    X, Y = np.meshgrid(xs, ys); P = np.stack([X.ravel(), Y.ravel()], 1)
    k = np.empty(len(P), int); d = np.empty(len(P))
    for c0 in range(0, len(P), 20000):
        d2 = ((P[c0:c0 + 20000, None, :] - line[None, :, :]) ** 2).sum(2); kc = d2.argmin(1); k[c0:c0 + 20000] = kc; d[c0:c0 + 20000] = np.sqrt(d2[np.arange(len(kc)), kc])
    w = hw[k]; hgt = hh[k]
    inner = np.array(p["inner"], float)
    inside = ((P - line[k]) * (inner - line[k])).sum(1) > 0
    u = np.clip(d / np.maximum(w, 0.5), 0, 4)
    # outside: a long gentle slope that reaches the hull at outer x the half width
    v = np.clip(u / p.get("outer", 1.0), 0, 1); outer_lift = hgt * (1 - v * v * (3 - 2 * v))
    kk = np.clip((u - p.get("wall", [0.78, 1.0])[0]) / (p.get("wall", [0.78, 1.0])[1] - p.get("wall", [0.78, 1.0])[0]), 0, 1); kk = kk * kk * (3 - 2 * kk); inner_lift = hgt * (1 - kk)
    lift = np.where(inside, inner_lift, outer_lift).reshape(X.shape)
    inside = inside.reshape(X.shape)
    if p.get("soften"):
        # smooth only the outer side; the inner side keeps its flat top and straight wall
        lift = np.where(inside, lift, blur(lift, p["soften"]))
    BAND_INSIDE[0] = inside
    return xs, ys, lift

for name, p in F.items():
    if name.startswith("_"): continue
    if p.get("type") == "band":
        xs, ys, h = band_field(p)
        region = grow(h > 0.3, 2)
    else:
      xs, ys, h, region = field_part(p)
    down = Vector((0, 0, -1)) if p["view"] == "above" else Vector((0, 0, 1))
    bm = bmesh.new(); grid = {}; FIXED = set()
    for side in (1, -1):
        for i in range(len(ys)):
            for j in range(len(xs)):
                if not region[i, j]: continue
                x = xs[j] * side
                if side < 0 and abs(xs[j]) < 1e-6: grid[(side, i, j)] = grid.get((1, i, j)); continue
                hit, n_, _, _ = tree.ray_cast(Vector((x, ys[i], 0)) - down * 3000, down, 6000)
                if hit is None: continue
                lift = h[i, j] if h[i, j] > 0.4 else -SINK
                # lift straight up/down for bands so their tops come out level, along the hull normal otherwise
                dirv = -down if p.get("type") == "band" else n_
                v_ = bm.verts.new(hit + dirv * lift); grid[(side, i, j)] = v_
                if p.get("type") == "band" and BAND_INSIDE[0][i, j] and h[i, j] > 0.3: FIXED.add(v_)
    for side in (1, -1):
        for i in range(len(ys) - 1):
            for j in range(len(xs) - 1):
                q = [grid.get((side, i, j)), grid.get((side, i, j + 1)), grid.get((side, i + 1, j + 1)), grid.get((side, i + 1, j))]
                if None in q or len(set(q)) < 4: continue
                bm.faces.new(q if side > 0 else q[::-1])
    if p.get("relax"):
        inner_v = [v for v in bm.verts if not v.is_boundary and v not in FIXED]
        for _ in range(p["relax"]):
            bmesh.ops.smooth_vert(bm, verts=inner_v, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.normal_update()
    if sum(fc.normal.dot(-down) for fc in bm.faces) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me)
    for pp in me.polygons: pp.use_smooth = True
    sc.collection.objects.link(bpy.data.objects.new(name, me))
    print("HP", name, len(me.polygons))
bpy.data.libraries.write(f"{D}/body_v2.blend", {sc}, fake_user=True)
