# Textures correlated with the original (asked: correlate the textures better between the equivalent parts of the source and our
# ship): every face of our piece looks up the nearest face of its equivalent in the original (REFERINTA: all of it, or the named
# objects for a decoration) and takes that face's material and UVs - each corner projected onto the plane of that original triangle,
# barycentric (extrapolated) UVs, so one face never straddles two UV islands. Symmetry: _S pieces look up as they are, _D pieces at
# their mirror (x -> -x), middle pieces at x -> -|x|, so both halves use the original's left half, mirrored.
# Decorations (named sources) are moved / bent on our ship, so there the lookup is by the piece's own frame seen from above: the
# fraction along its main axis and across it, put at the same fractions in the source and dropped onto its top (ray from above).
# Hull pieces: the original surface hit by a ray along our face's normal (from RAY m outside inwards, then inwards from the face),
# facing the same way (cos > COSN); the nearest face only when no ray hits.
# Ship coords: our pieces = world + X0 on x; the original = world.
# Usage: blender -b <f.blend> --python texturi_din_original.py -- <out.blend> <x0> <target[,target...]=*|src[+src...]> ...
#        env EXCLUDE = name prefixes left out of the general source (default: blades + decorations)
#        target = an object name or a prefix ending in * (an_decor_R060_* = both sides)
#        env SINGLE=1: one texture per piece (asked: every piece has a single texture, no patches of other ones) - the material
#        covering most of the piece's area in a first pass, then the lookup redone against that material's triangles only;
#        env MAT="piece:material,..." forces the material of a piece (exact name or prefix ending in *)
import bpy, sys, os, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT, X0 = a[0], float(a[1])
RAY, COSN = float(os.environ.get("RAY", "40")), float(os.environ.get("COSN", "0.5"))
import os
EXCL = os.environ.get("EXCLUDE", "Circle,R031,R100,R131,R060,R109,R108,R121,R122").split(",")
# the blades (moving, red) and the decorations are not hull: kept out of the general source
REF = [o for o in bpy.data.collections["REFERINTA"].all_objects if o.type == "MESH" and not o.name.startswith(tuple(EXCL))
       and not any(m and m.name.startswith("lame") for m in o.data.materials)]
cache = {}
def source(spec):
    if spec in cache: return cache[spec]
    obs = REF if spec == "*" else [bpy.data.objects[n] for n in spec.split("+")]
    V, T, TUV, TM = [], [], [], []
    for o in obs:
        me = o.data; M = o.matrix_world; uvl = me.uv_layers.active
        if uvl is None: continue
        base = len(V); V += [tuple(M @ v.co) for v in me.vertices]
        for p in me.polygons:
            mat = me.materials[p.material_index] if p.material_index < len(me.materials) else None
            if mat is None: continue
            ls = list(p.loop_indices)
            for i in range(1, len(ls) - 1):
                tri = (ls[0], ls[i], ls[i + 1]); T.append([base + me.loops[l].vertex_index for l in tri])
                TUV.append([tuple(uvl.data[l].uv) for l in tri]); TM.append(mat.name)
    V = np.array(V); T = np.array(T); bvh = BVHTree.FromPolygons([Vector(p) for p in V], T.tolist())
    cache[spec] = (V, T, np.array(TUV), TM, bvh); print("SURSA", spec[:60], len(T), "triunghiuri"); return cache[spec]
def bary(p, A, B, C):
    v0, v1, v2 = B - A, C - A, p - A; d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1; d20, d21 = v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01 or 1e-12; v = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den; return 1 - v - w, v, w
targets = []
for spec in a[2:]:
    tg, src = spec.split("=")
    for t in tg.split(","):
        names = [o.name for o in bpy.data.collections["ASAMBLAT_NOU"].all_objects if o.type == "MESH" and (o.name.startswith(t[:-1]) if t.endswith("*") else o.name == t)]
        targets += [(n, src) for n in names]
SINGLE = os.environ.get("SINGLE", "0") == "1"
FORCE = [kv.split(":") for kv in os.environ.get("MAT", "").split(",") if kv]
def only(src, mat):
    k = (src, mat)
    if k not in cache:
        V, T, TUV, TM, _ = source(src); sel = np.array([m == mat for m in TM])
        cache[k] = (V, T[sel], TUV[sel], [mat] * int(sel.sum()), BVHTree.FromPolygons([Vector(p) for p in V], T[sel].tolist()))
    return cache[k]
def transfer(name, src, V, T, TUV, TM, bvh):
    o = bpy.data.objects[name]; me = o.data
    side = "D" if name.endswith("_D") else "S" if name.endswith("_S") else "M"
    W = np.array([tuple(o.matrix_world @ v.co) for v in me.vertices]) + [X0, 0, 0]; RW = np.array(o.matrix_world.to_3x3())
    def look(p):
        q = p.copy()
        if side == "D": q[0] = -q[0]
        elif side == "M": q[0] = -abs(q[0])
        return q
    if src != "*":
        def frame(P):
            c = P[:, :2].mean(0); _, _, Vt = np.linalg.svd(P[:, :2] - c); ax = Vt[0] * (np.sign(Vt[0][1]) or 1); nr = np.array([-ax[1], ax[0]])
            pr, pe = (P[:, :2] - c) @ ax, (P[:, :2] - c) @ nr; return c, ax, nr, pr.min(), pr.max(), np.abs(pe).max()
        Wm = W.copy()
        if side == "D": Wm[:, 0] = -Wm[:, 0]
        ft, fs = frame(Wm), frame(V); ztop = V[:, 2].max() + 100
        def look_frame(p):
            q = p.copy()
            if side == "D": q[0] = -q[0]
            c, ax, nr, a0, a1, h = ft; u = ((q[:2] - c) @ ax - a0) / (a1 - a0); w = ((q[:2] - c) @ nr) / h
            c2, ax2, nr2, b0, b1, h2 = fs; xy = c2 + ax2 * (b0 + u * (b1 - b0)) + nr2 * (w * h2); return np.r_[xy, ztop]
    mats = sorted(set(TM)); me.materials.clear()
    for m in mats: me.materials.append(bpy.data.materials[m])
    mi = {m: i for i, m in enumerate(mats)}
    uvl = me.uv_layers.active or me.uv_layers.new(name="UVMap")
    nl = len(me.loops); uv = np.zeros((nl, 2)); midx = np.zeros(len(me.polygons), np.int32); far = 0
    li = np.zeros(nl, np.int32); me.loops.foreach_get("vertex_index", li)
    for p in me.polygons:
        ls = list(p.loop_indices)
        if src != "*":
            hit = bvh.ray_cast(Vector(look_frame(W[li[ls]].mean(0))), Vector((0, 0, -1)))
            if hit[0] is None: hit = bvh.find_nearest(Vector(look_frame(W[li[ls]].mean(0))[:2].tolist() + [V[:, 2].mean()]))
            if hit[0] is None: continue
            k = hit[2]; midx[p.index] = mi[TM[k]]; A, B, C = V[T[k]]
            for l in ls:
                q = look_frame(W[li[l]]); q[2] = 0; n = np.cross(B - A, C - A); n /= np.linalg.norm(n) or 1
                q[2] = A[2] - (n[0] * (q[0] - A[0]) + n[1] * (q[1] - A[1])) / (n[2] if abs(n[2]) > 0.05 else 0.05)
                u, v, w = bary(q, A, B, C); uv[l] = u * TUV[k][0] + v * TUV[k][1] + w * TUV[k][2]
            continue
        c = look(W[li[ls]].mean(0)); n0 = np.array(p.normal[:]) @ RW.T; n0 /= np.linalg.norm(n0) or 1
        if side == "D" or (side == "M" and W[li[ls]].mean(0)[0] > 0): n0[0] = -n0[0]
        hit = (None,)
        for sg in (1, -1):      # the original surface seen along our face's normal (outside first), facing the same way
            h = bvh.ray_cast(Vector(c + n0 * RAY), Vector(-n0), 2 * RAY) if sg == 1 else bvh.ray_cast(Vector(c - n0 * 0.01), Vector(-n0), RAY)
            if h[0] is not None and np.dot(np.array(h[1][:]), n0) > COSN: hit = h; break
        if hit[0] is None: hit = bvh.find_nearest(Vector(c))
        if hit[0] is None: continue
        k = hit[2]; far = max(far, hit[3]); midx[p.index] = mi[TM[k]]
        A, B, C = V[T[k]]
        for l in ls:
            u, v, w = bary(look(W[li[l]]), A, B, C); uv[l] = u * TUV[k][0] + v * TUV[k][1] + w * TUV[k][2]
    uvl.data.foreach_set("uv", uv.ravel().astype(np.float32)); me.polygons.foreach_set("material_index", midx)
    area = np.zeros(len(me.polygons)); me.polygons.foreach_get("area", area)
    cnt = np.bincount(midx, minlength=len(mats)); print("TEXTURA", name, side, "<-", src[:40], "| fete pe materiale", dict(zip(mats, cnt.tolist())), "| distanta max %.1f m" % far)
    return mats[int(np.argmax(np.bincount(midx, weights=area, minlength=len(mats))))]
for name, src in targets:
    mat = transfer(name, src, *source(src))
    if SINGLE:
        for k, m in FORCE:
            if (name.startswith(k[:-1]) if k.endswith("*") else name == k): mat = m
        print("O TEXTURA", name, "->", mat); transfer(name, src, *only(src, mat))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
