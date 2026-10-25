# V7 body pass (the user's 2026-10-25 notes on the exploded V6): the aft body evened out (no "hips": the width falls
# smoothly from mid-body to the stern), the rear deck C22 rebuilt with the crescent's horseshoe as its front end and a
# shorter tail (C16 removed, it is now part of the deck), the decorations re-seated on the new deck, the dome C4 moved
# aft and the stern window C12 shrunk to sit inside the stern frame C8.
# Usage: blender -b --python v7_body.py
import bpy, bmesh, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
P = json.load(open(f"{D}/body/parts.json")); K = json.load(open(f"{D}/trace/v7_body.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]
def world(o): M = np.array(o.matrix_world); v = np.array([x.co for x in o.data.vertices]); return v @ M[:3, :3].T + M[:3, 3]
def put(o, v):
    Mi = np.array(o.matrix_world.inverted()); loc = v @ Mi[:3, :3].T + Mi[:3, 3]
    for x, p in zip(o.data.vertices, loc): x.co = p.tolist()
    o.data.update()
def tree(names):
    b = bmesh.new()
    for n in names:
        o = sc.objects[n]; k = len(b.verts); b.from_mesh(o.data); b.verts.ensure_lookup_table()
        for v in b.verts[k:]: v.co = o.matrix_world @ v.co
    return BVHTree.FromBMesh(b)
def top(t, x, y):
    h = t.ray_cast(Vector((x, y, 3000)), Vector((0, 0, -1))); return h[0].z if h[0] is not None else None
def relax(o, dz, n=12):
    nb = [[] for _ in dz]
    for e in o.data.edges: a, b = e.vertices; nb[a].append(b); nb[b].append(a)
    for _ in range(n): dz = [0.5 * d + 0.5 * (sum(dz[j] for j in q) / len(q)) if q else d for d, q in zip(dz, nb)]
    return np.array(dz)
log = []
# parts the user had removed (C16 lives on as the deck's horseshoe front, C1 and C14 were dropped on 2026-10-25)
for name in K.get("remove", []):
    o = sc.objects.get(name)
    if o is not None: bpy.data.objects.remove(o); log.append("removed " + name)

# 1. (optional) even aft body: half width eases from its mid-body value at y0 down to `stern_half` at y1, the stern's own rounding kept
E = K.get("even")   # off since the user asked for V4's plain body (no section set in v7_body.json)
if E:
    gy = np.arange(-1000, 1000.1, 5.0); v = world(sc.objects["corp"]); wc = np.full(len(gy), np.nan)
    idx = np.round((v[:, 1] - gy[0]) / 5).astype(int)
    for k in np.unique(idx): wc[k] = np.abs(v[idx == k, 0]).max()
    w0 = float(np.interp(E["y0"], gy, wc)); u = np.clip((E["y0"] - gy) / (E["y0"] - E["y1"]), 0, 1)
    wt = w0 - (w0 - E["stern_half"]) * u ** E["power"]
    keep = np.clip((gy - E["tip"]) / (E["tip_fade"]), 0, 1)                 # 0 at the very stern: its rounding is left alone
    s = np.where(np.isnan(wc) | (gy > E["y0"]), 1, np.clip(wt / wc, 0.8, 1.2)); s = 1 + (s - 1) * keep
    k = np.exp(-0.5 * (np.arange(-15, 16) / 5) ** 2); s = np.convolve(np.pad(s, 15, mode="edge"), k / k.sum(), "valid")
    for o in sc.objects:
        if o.type == "MESH" and P.get(o.name, ["?"])[0].startswith("C"):
            v = world(o); v[:, 0] *= np.interp(v[:, 1], gy, s); put(o, v)
    log.append("even x%.2f..%.2f" % (s.min(), s.max()))

# 2. the deck rebuilt over the evened body: plan outline from v7_body.json (front = the crescent's horseshoe), a crisp
# rim at the horseshoe, the horns tapering down like the crescent did, and the height fading where the body turns down
old_deck = tree(["corp", "rear_deck"]); C = K["deck"]
for o in [o for o in sc.objects if o.name == "rear_deck"]: bpy.data.objects.remove(o)
body = tree(["corp"])
def rounded(outline, n=480, r=0.3):
    Pt = np.array(outline, float); Pt = np.vstack([Pt, Pt[:1]]); seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Pt, axis=0), axis=1))]
    t = np.linspace(0, seg[-1], n, endpoint=False); Q = np.stack([np.interp(t, seg, Pt[:, c]) for c in (0, 1)], 1)
    sig = max(r * n / len(outline) / 2, 0.5); g = np.exp(-0.5 * (np.arange(-int(3 * sig), int(3 * sig) + 1) / sig) ** 2); g /= g.sum(); m = len(g) // 2
    return np.stack([np.convolve(np.r_[Q[-m:, c], Q[:, c], Q[:m, c]], g, "valid") for c in (0, 1)], 1)
def sdist(O, X, Y):
    A = O[None, None]; B = np.roll(O, -1, 0)[None, None]; Ed = B - A; Pq = np.stack([X, Y], -1)[:, :, None]
    t = np.clip(((Pq - A) * Ed).sum(-1) / (Ed * Ed).sum(-1), 0, 1); d = np.linalg.norm(Pq - (A + Ed * t[..., None]), axis=-1).min(-1)
    a, b2 = A[..., 1], B[..., 1]; xi = (B[..., 0] - A[..., 0]) * (Y[..., None] - a) / np.where(b2 == a, 1e-9, b2 - a) + A[..., 0]
    ins = (((a > Y[..., None]) != (b2 > Y[..., None])) & (X[..., None] < xi)).sum(-1) % 2 == 1
    return np.where(ins, d, -d)
half = np.array(C["outline"], float); O = rounded(np.vstack([half, half[::-1] * [-1, 1]]).tolist(), r=C["round"]); Mg = C["apron"] + 20
xs = np.arange(O[:, 0].min() - Mg, O[:, 0].max() + Mg, 2.0); ys = np.arange(O[:, 1].min() - Mg, O[:, 1].max() + Mg, 2.0); X, Y = np.meshgrid(xs, ys)
f = np.clip((Y - C["front"][0]) / (C["front"][1] - C["front"][0]), 0, 1)        # 0 aft, 1 at the horseshoe
apron = C["apron"] + (C["front_apron"] - C["apron"]) * f; rim = C["rim"] + (C["front_rim"] - C["rim"]) * f
d = sdist(O, X, Y); q = np.clip((d + apron) / (apron + rim), 0, 1); L = C["height"] * q * q * (3 - 2 * q)
h = np.clip((Y - C["horns"][0]) / (C["horns"][1] - C["horns"][0]), 0, 1); L = L * (1 - (1 - C["horn_tip"]) * h * h * (3 - 2 * h))
L = L * np.clip((Y - C["stern_fade"][0]) / (C["stern_fade"][1] - C["stern_fade"][0]), 0, 1) ** 0.6
HIT = {}; NZ = np.zeros(L.shape)
for i in range(len(ys)):
    for j in range(len(xs)):
        hit, nrm, _, _ = body.ray_cast(Vector((xs[j], ys[i], 900)), Vector((0, 0, -1)), 1800)
        if hit is not None and nrm.z >= 0.15: HIT[(i, j)] = (hit, nrm); NZ[i, j] = nrm.z
# flattens onto the flanks (no lip in plan); that fade is blurred so it runs smooth across the grid
Fl = np.clip((NZ - C["flank"][0]) / (C["flank"][1] - C["flank"][0]), 0, 1)
g = np.exp(-0.5 * (np.arange(-9, 10) / 3.0) ** 2); g /= g.sum()
for ax in (0, 1): Fl = np.apply_along_axis(lambda r: np.convolve(np.pad(r, 9, mode="edge"), g, "valid"), ax, Fl)
Lf = L * Fl                                   # only the flank fade is blurred: the crescent's rim stays crisp
bm = bmesh.new(); G = {}
for (i, j), (hit, nrm) in HIT.items():
    lift = float(Lf[i, j]); G[(i, j)] = (hit, nrm, lift + 0.3 - 3.3 * (1 - min(1.0, lift / 2.0)) ** 2)
# from flat[0] to flat[1] the top turns into a level plane at the deck's height over the centreline (the crescent
# reads flat), its rim dropping to the body in proportion to the lift so the edge stays a smooth slope
def level(y):
    h = body.ray_cast(Vector((0, y, 900)), Vector((0, 0, -1)), 1800)[0]; return (h.z if h is not None else 0.0) + C["height"]
V = {}
for key, (hit, nrm, lift) in G.items():
    w = min(1.0, max(0.0, (hit.y - C["flat"][0]) / (C["flat"][1] - C["flat"][0]))) if "flat" in C else 0.0
    p = hit + nrm * lift
    if w > 0: p = p * (1 - w) + (hit + Vector((0, 0, (level(hit.y) - hit.z) * max(lift, -3.0) / C["height"]))) * w
    V[key] = bm.verts.new(p)
for (i, j) in list(V):
    qd = [V.get((i, j)), V.get((i, j + 1)), V.get((i + 1, j + 1)), V.get((i + 1, j))]
    if None not in qd: bm.faces.new(qd)
for _ in range(3): bmesh.ops.smooth_vert(bm, verts=[x for x in bm.verts if not x.is_boundary], factor=0.4, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); me = bpy.data.meshes.new("rear_deck"); bm.to_mesh(me)
for p in me.polygons: p.use_smooth = True
sc.collection.objects.link(bpy.data.objects.new("rear_deck", me)); log.append("deck %d faces" % len(me.polygons))

# 3. decorations re-seated: each point moves by the change of the deck top under it
new_deck = tree(["corp", "rear_deck"])
for name in K["lift"]:
    o = sc.objects.get(name)
    if o is None: continue
    v = world(o); dz = []
    for p in v:
        a, b = top(old_deck, p[0], p[1]), top(new_deck, p[0], p[1]); dz.append(b - a if a is not None and b is not None else 0.0)
    dz = relax(o, dz); v[:, 2] += dz; put(o, v); log.append("%s %+.0f..%+.0f" % (name, dz.min(), dz.max()))

# 4. the dome moved aft, following the deck surface
o = sc.objects["dorsal_dome"]; v = world(o); dy = K["dome_dy"]
dz = [((top(new_deck, p[0], p[1] + dy) or 0) - (top(new_deck, p[0], p[1]) or 0)) for p in v]
v[:, 1] += dy; v[:, 2] += relax(o, dz); put(o, v); log.append("dome dy %+.0f" % dy)

# 5. the stern window C12 as a flat plate ("a pancake") filling the stern frame C8's opening: a superellipse like the
# frame, its face a constant stand-off from the stern face, its edge rounding down into the hull
FR = json.load(open(f"{D}/body/frames.json"))["stern_frame"]; W = K["window"]; fr = world(sc.objects["stern_frame"])
cz = (fr[:, 2].min() + fr[:, 2].max()) / 2; hx = FR["half_w"] - FR["tube"] - W["gap"]; hz = FR["half_h"] - FR["tube"] - W["gap"]
sc_body = tree(["corp"]); bm = bmesh.new(); NR, NA = 24, 96; rings = []
for i in range(NR + 1):
    r = i / NR; row = []
    for k in range(NA):
        a = 2 * np.pi * k / NA; c, sn = np.cos(a), np.sin(a)
        x = hx * r * np.sign(c) * abs(c) ** (2 / FR["n"]); z = cz + hz * r * np.sign(sn) * abs(sn) ** (2 / FR["n"])
        hit = sc_body.ray_cast(Vector((x, -3000, z)), Vector((0, 1, 0)), 6000)[0]
        y = hit.y if hit is not None else -780.0
        e = max(0.0, (r - W["edge"]) / (1 - W["edge"])); off = W["thick"] * np.sqrt(max(0.0, 1 - e * e)) - 1.0 * (r >= 1)
        row.append(bm.verts.new((x, y - off, z)))
    rings.append(row)
ctr = bm.verts.new(rings[0][0].co)
for k in range(NA): bm.faces.new((ctr, rings[1][k], rings[1][(k + 1) % NA]))
for A, B in zip(rings[1:], rings[2:]):
    for k in range(NA): bm.faces.new((A[k], B[k], B[(k + 1) % NA], A[(k + 1) % NA]))
for v_ in rings[0]:
    if v_ is not ctr and not v_.link_faces: bm.verts.remove(v_)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.normal_update()
if sum(f.normal.y for f in bm.faces) > 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
bpy.data.objects.remove(sc.objects["stern_window"]); me = bpy.data.meshes.new("stern_window"); bm.to_mesh(me)
for p in me.polygons: p.use_smooth = True
sc.collection.objects.link(bpy.data.objects.new("stern_window", me)); log.append("window plate %.0fx%.0f" % (2 * hx, 2 * hz))

# 6. the stern eyes C13/C13b as true rings: a round tube along the circle (paths.json) laid onto the stern face, half sunk
PJ = json.load(open(f"{D}/body/paths.json"))
for name, tube in K["rings"].items():
    cx, cz, r = PJ[name]["circle"]; bm = bmesh.new(); NA, NT = 96, 16
    for side in (1, -1):
        rows = []
        for k in range(NA):
            a = 2 * np.pi * k / NA; x, z = side * (cx + r * np.cos(a)), cz + r * np.sin(a)
            hit, n, _, _ = sc_body.ray_cast(Vector((x, -3000, z)), Vector((0, 1, 0)), 6000)
            if hit is None: hit, n = Vector((x, -780, z)), Vector((0, -1, 0))
            rad = Vector((np.cos(a) * side, 0, np.sin(a))); rad = (rad - n * rad.dot(n)).normalized()
            c = hit + n * (tube * (1 - K["ring_sink"]))
            rows.append([bm.verts.new(c + (rad * np.cos(b) + n * np.sin(b)) * tube) for b in 2 * np.pi * np.arange(NT) / NT])
        for k in range(NA):
            A, B = rows[k], rows[(k + 1) % NA]
            for j in range(NT): bm.faces.new((A[j], A[(j + 1) % NT], B[(j + 1) % NT], B[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); o = sc.objects.get(name)
    if o: bpy.data.objects.remove(o)
    me = bpy.data.meshes.new(name); bm.to_mesh(me)
    for p in me.polygons: p.use_smooth = True
    sc.collection.objects.link(bpy.data.objects.new(name, me)); log.append("%s ring r%.0f tube %.1f" % (name, r, tube))
# 7. fairings built over the analytic body re-seated on the fitted skin: per 5 m slice and side, the slice moves out
# along the skin normal until its lowest edge is sunk by `sink` again (the skin had grown over them)
R = K["reseat"]
for name in R["parts"]:
    o = sc.objects.get(name)
    if o is None: continue
    v = world(o); nrm = np.zeros_like(v); dd = np.zeros(len(v))
    for n, p in enumerate(v):
        loc, nn, _, _ = sc_body.find_nearest(Vector(p.tolist())); nrm[n] = nn; dd[n] = (Vector(p.tolist()) - loc).dot(nn)
    key = np.round(v[:, 1] / 5).astype(int) * 2 + (v[:, 0] > 0); delta = np.zeros(len(v))
    for k in np.unique(key): m = key == k; delta[m] = max(0.0, -R["sink"] - dd[m].min())
    delta = relax(o, delta.tolist(), 20); v += nrm * delta[:, None]; put(o, v); log.append("%s reseat +%.0f" % (name, delta.max()))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True); print("V7 BODY", "; ".join(log))
