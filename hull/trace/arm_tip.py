# The front arm ahead of the nacelle: a closed tube from where the arm surface leaves the nacelle's tip to the arm's
# point. Construction:
#  * the first ring = the arm surface's front edge (its first section, end2 -> end1 around the arm) closed by the nacelle's
#    outer side at the same section (end1 -> end2), so the tube starts exactly on the arm surface and the nacelle;
#  * the path = the arm's centre curve (principal curve, arm_slices.py) from the nearest point to that ring to the arm's
#    end, continued to the arm's farthest vertex; planes perpendicular to it every ~1.5 m;
#  * each ring = the reference arm (main island) cut by the plane, a radius per angle around the path point over the
#    full turn, angles without surface (holes) interpolated around the turn, resampled at equal arc length; the angle
#    measured from a frame carried along the path without twist (parallel transport), started on the first ring's
#    first point, so ring i point j are the same place along the arm;
#  * smoothed around and along (gaussian), the first ring pinned (flush with arm and nacelle), the last ring closed into
#    the arm's point; one side, mirrored.
# Usage: blender -b <arm.blend> --python arm_tip.py -- <arm_dbg.npz> <nacelle_sections.npy> <centre.npy> <out.blend> <dx>
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; D = np.load(a[0]); G = np.load(a[1]); CD = np.load(a[2]); OUT, DX = a[3], float(a[4])
sc = bpy.context.scene; X0 = D["X"][0]; S = D["G"][0]; M = S.shape[0]; H = M // 2; NA = 200; NR = 720; STEP = 1.5
CD = CD + [-DX, 0, 0] if np.abs(CD[:, 0].mean() - X0[:, 0].mean()) > 800 else CD   # centre curve into the nacelle's frame
o = bpy.data.objects["brat_fata_022_S"]; bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
seen, best = set(), []
for f in bm.faces:
    if f.index in seen: continue
    st, isl = [f], []
    while st:
        g = st.pop()
        if g.index in seen: continue
        seen.add(g.index); isl.append(g); st += [h for e in g.edges for h in e.link_faces if h.index not in seen]
    if len(isl) > len(best): best = isl
P = np.array([v.co for v in bm.verts]) - [DX, 0, 0]
T = np.array([[f.verts[0].index, f.verts[i].index, f.verts[i + 1].index] for f in best for i in range(1, len(f.verts) - 1)]); used = np.unique(T)
def cut(o_, n):
    d = (P - o_) @ n; dd = d[T]; sel = (dd.min(1) < 0) & (dd.max(1) > 0); out = []
    for t, x in zip(T[sel], dd[sel]):
        for p_, q_ in ((0, 1), (1, 2), (2, 0)):
            if (x[p_] > 0) != (x[q_] > 0): w = x[p_] / (x[p_] - x[q_]); out.append(P[t[p_]] * (1 - w) + P[t[q_]] * w)
    return np.array(out)
FRAC = None                                                                  # arc-length fractions of the first ring's points
def resample_closed(Y, n):
    Z = np.vstack([Y, Y[:1]]); l = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Z, axis=0), axis=1))]; t = FRAC * l[-1] if FRAC is not None else np.linspace(0, l[-1], n + 1)[:-1]
    return np.array([np.interp(t, l, Z[:, c]) for c in range(3)]).T
# first ring: arm front edge (end2 -> end1) + the nacelle's outer side (end1 -> end2)
cX = X0.mean(0); hA, hB = S[0:H], S[H:M][::-1]                             # both outline halves, end1 -> end2
side = hA if np.mean(np.linalg.norm(hA - cX, axis=1)) > np.mean(np.linalg.norm(hB - cX, axis=1)) else hB   # the outer one (outside the loop)
ring0 = np.vstack([X0, side[1:-1]]); c_r0 = ring0.mean(0)
# path: from the centre-curve point nearest the first ring, toward the end farther from the nacelle's back
i0 = int(np.argmin(np.linalg.norm(CD - c_r0, axis=1))); back = D["G"][-1].mean(0)
path = CD[i0:] if np.linalg.norm(CD[-1] - back) > np.linalg.norm(CD[0] - back) else CD[:i0 + 1][::-1]
tip = P[used][np.argmax((P[used] - path[-1]) @ (path[-1] - path[-10]))]; path = np.vstack([path, tip])
l = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]; ns = int(l[-1] / STEP); ts = np.linspace(0, l[-1], ns)
path = np.array([np.interp(ts, l, path[:, c]) for c in range(3)]).T; tg = np.gradient(path, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]
# the first ring's own plane normal decides the path's start direction; blend the path start onto the ring's centre
n0 = np.linalg.svd(ring0 - c_r0)[2][2]; n0 *= np.sign(np.dot(n0, tg[0]))
r = ring0[0] - c_r0; r -= np.dot(r, n0) * n0; r /= np.linalg.norm(r)
if np.dot(np.cross(n0, ring0[0] - c_r0), ring0[len(X0) // 2] - c_r0) < 0: ring0 = np.vstack([ring0[:1], ring0[1:][::-1]])   # turning +angle about n0
# the first ring keeps its own points (the arm edge's vertices, so the two weld), every ring uses its arc-length fractions
NA = len(ring0); Z0 = np.vstack([ring0, ring0[:1]]); l0 = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Z0, axis=0), axis=1))]; FRAC = l0[:-1] / l0[-1]
rings = [ring0.copy()]; holes = []; frames = []
for k in range(1, ns - 1):
    t_ = tg[k]; r = r - np.dot(r, t_) * t_; r /= np.linalg.norm(r); v = np.cross(t_, r); frames.append((path[k], t_, r, v))
    Q = cut(path[k], t_); Q = Q[np.linalg.norm(Q - path[k], axis=1) < 200] if len(Q) else Q
    if len(Q) < 8: break
    q2 = np.stack([(Q - path[k]) @ r, (Q - path[k]) @ v], 1); aq = np.arctan2(q2[:, 1], q2[:, 0]) % (2 * np.pi); rq = np.linalg.norm(q2, axis=1)
    th = np.linspace(0, 2 * np.pi, NR, endpoint=False); rad = np.full(NR, np.nan)
    for i, t in enumerate(th):
        dt = np.abs((aq - t + np.pi) % (2 * np.pi) - np.pi); m = dt < 2.5 * np.pi / NR
        if m.sum(): rad[i] = np.median(rq[m])
    ok = ~np.isnan(rad); holes.append(int((~ok).sum()))
    if ok.sum() < NR * 0.3: break
    rad = np.interp(np.arange(NR), np.where(ok)[0], rad[ok], period=NR)
    ring = path[k] + np.cos(th)[:, None] * rad[:, None] * r + np.sin(th)[:, None] * rad[:, None] * v
    rings.append(resample_closed(ring, NA))
X = np.array(rings)
def gs(y, sg, axis, wrap=False):
    k = np.exp(-0.5 * (np.arange(-3 * sg, 3 * sg + 1) / sg) ** 2); k /= k.sum()
    pad = (lambda z: np.pad(z, 3 * sg, mode="wrap")) if wrap else (lambda z: np.pad(z, 3 * sg, mode="edge"))
    return np.apply_along_axis(lambda z: np.convolve(pad(z), k, "valid"), axis, y)
first = X[0].copy(); X = gs(gs(X, 3, 1, True), 10, 0)
w = np.exp(-np.arange(len(X)) / 40.0)[:, None, None]; X = X + w * (first - X[0])[None]   # first ring exactly on the arm + nacelle
tipp = path[min(len(rings) + 1, ns - 1)]
V = np.vstack([X.reshape(-1, 3), tipp[None]]); L = len(X)
F = [(k * NA + i, k * NA + (i + 1) % NA, (k + 1) * NA + (i + 1) % NA, (k + 1) * NA + i) for k in range(L - 1) for i in range(NA)]
F += [((L - 1) * NA + i, (L - 1) * NA + (i + 1) % NA, L * NA) for i in range(NA)]
mt = bpy.data.materials.get("brat_gri") or bpy.data.materials.new("brat_gri")
col = bpy.data.collections.get("BRAT_NOU") or bpy.data.collections.new("BRAT_NOU")
for s_ in (1, -1):
    W = V.copy(); W[:, 0] *= s_; me = bpy.data.meshes.new("varf"); me.from_pydata((W + [DX, 0, 0]).tolist(), [], F if s_ > 0 else [f[::-1] for f in F]); me.materials.append(mt)
    for p_ in me.polygons: p_.use_smooth = True
    b2 = bmesh.new(); b2.from_mesh(me); bmesh.ops.recalc_face_normals(b2, faces=b2.faces); b2.to_mesh(me); b2.free()
    col.objects.link(bpy.data.objects.new("brat_varf%s" % ("_S" if s_ > 0 else "_D"), me))
# arm surface + tube welded into one object per side (the arm's front edge = the tube's first ring)
for sfx in ("_S", "_D"):
    A_, B_ = bpy.data.objects["brat_nou" + sfx], bpy.data.objects["brat_varf" + sfx]; me = bpy.data.meshes.new("brat_fata" + sfx); me.materials.append(mt)
    Vs = [tuple(v.co) for v in A_.data.vertices] + [tuple(v.co) for v in B_.data.vertices]; nA = len(A_.data.vertices)
    Fs = [tuple(p_.vertices) for p_ in A_.data.polygons] + [tuple(nA + x for x in p_.vertices) for p_ in B_.data.polygons]
    me.from_pydata(Vs, [], Fs)
    for p_ in me.polygons: p_.use_smooth = True
    b2 = bmesh.new(); b2.from_mesh(me); bmesh.ops.remove_doubles(b2, verts=b2.verts, dist=0.01); bmesh.ops.recalc_face_normals(b2, faces=b2.faces); b2.to_mesh(me)
    bnd = sum(1 for e in b2.edges if e.is_boundary); b2.free(); ob = bpy.data.objects.new("brat_fata" + sfx, me); col.objects.link(ob)
    bk = bpy.data.collections.get("BRAT_PIESE") or bpy.data.collections.new("BRAT_PIESE")
    if bk.name not in sc.collection.children: sc.collection.children.link(bk)
    for o_ in (A_, B_): col.objects.unlink(o_); bk.objects.link(o_)
    print("OBIECT %s: %d varfuri, %d fete, muchii libere %d (marginile spre nacela si spre corp)" % (ob.name, len(me.vertices), len(me.polygons), bnd))
bpy.context.view_layer.layer_collection.children["BRAT_PIESE"].exclude = True
dj = np.gradient(X, axis=0); di = np.roll(X, -1, 1) - np.roll(X, 1, 1); nn = np.cross(di, dj); nn /= np.linalg.norm(nn, axis=2)[:, :, None]
turn = np.degrees(np.arccos(np.clip(np.sum(nn[1:] * nn[:-1], axis=2), -1, 1)))
print("VARF BRAT: %d inele pe %.0f m (pana la varful bratului), %d puncte pe inel; goluri inchise (unghiuri fara suprafata, medie pe inel) %.0f din %d; primul inel pe brat+nacela: abatere %.3f m; rotire normala intre inele max %.2f (p99 %.2f); unghi intre planul primului inel si drum %.1f grade"
      % (L, l[-1], NA, np.mean(holes) if holes else 0, NR, np.max(np.linalg.norm(X[0] - first, axis=1)), turn.max(), np.percentile(turn, 99), np.degrees(np.arccos(abs(np.dot(n0, tg[0]))))))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
