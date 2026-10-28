# The whole front arm as ONE sequence of rings, from the arm/body side (section J1 of the nacelle) to the arm's point, so
# the part along the nacelle and the tube ahead of it are smoothed together (no seam where they meet). Construction:
#  * along the nacelle: ring = the arm surface's section (arm_shell.py, end2 -> end1 around the arm) + the nacelle's
#    outer outline half (end1 -> end2); the nacelle points stay exactly where they are, no faces are made over them;
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
# Usage: blender -b <arm.blend> --python arm_full.py -- <arm_dbg.npz> <nacelle_sections.npy> <centre.npy> <out.blend> <dx>
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; D = np.load(a[0]); G = np.load(a[1]); CD = np.load(a[2]); OUT, DX = a[3], float(a[4])
sc = bpy.context.scene; X0 = D["X"][0]; S = D["G"][0]; M = S.shape[0]; H = M // 2; NA = 200; NR = 720; STEP = 1.5; BLEND = 60.0
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
# rings along the nacelle (front first): arm curve + the nacelle's outer half, the half chosen once for all sections
XN = D["X"]; GN = D["G"]; K = len(XN); NAa = XN.shape[1]
OPN = D["OPEN"] if "OPEN" in D.files else np.zeros((K, NAa), bool)
cX = XN[0].mean(0); useA = np.mean(np.linalg.norm(GN[0][0:H] - cX, axis=1)) > np.mean(np.linalg.norm(GN[0][H:M][::-1] - cX, axis=1))
half = lambda S_: (S_[0:H] if useA else S_[H:M][::-1])[1:-1]
RN = np.array([np.vstack([XN[k], half(GN[k])]) for k in range(K)]); NA = RN.shape[1]; NH = NA - NAa
ring0 = RN[0]; c_r0 = ring0.mean(0)
# path: from the centre-curve point nearest the first ring, toward the end farther from the nacelle's back
i0 = int(np.argmin(np.linalg.norm(CD - c_r0, axis=1))); back = GN[-1].mean(0)
path = CD[i0:] if np.linalg.norm(CD[-1] - back) > np.linalg.norm(CD[0] - back) else CD[:i0 + 1][::-1]
tip = P[used][np.argmax((P[used] - path[-1]) @ (path[-1] - path[-10]))]; path = np.vstack([path, tip])
n0_ = np.linalg.svd(ring0 - c_r0)[2][2]; n0_ *= np.sign(np.dot(n0_, path[-1] - c_r0))
path = np.vstack([c_r0, path[(path - c_r0) @ n0_ > STEP]])                # the path starts at the junction ring's centre
l = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]; ns = int(l[-1] / STEP); ts = np.linspace(0, l[-1], ns)
path = np.array([np.interp(ts, l, path[:, c]) for c in range(3)]).T
# the path smoothed (gaussian, ~SMP m) except its two ends, so the cutting planes never pivot around a point of the ring
SMP = 40.0; sgp = max(1, int(SMP / STEP)); kp = np.exp(-0.5 * (np.arange(-3 * sgp, 3 * sgp + 1) / sgp) ** 2); kp /= kp.sum()
ps = np.array([np.convolve(np.pad(path[:, c], 3 * sgp, mode="reflect", reflect_type="odd"), kp, "valid") for c in range(3)]).T
wp = np.clip(np.minimum(ts, ts[-1] - ts) / (2 * SMP), 0, 1)[:, None]; path = path * (1 - wp) + ps * wp
tg = np.gradient(path, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]
n0 = np.linalg.svd(ring0 - c_r0)[2][2]; n0 *= np.sign(np.dot(n0, tg[0]))
r = ring0[0] - c_r0; r -= np.dot(r, n0) * n0; r /= np.linalg.norm(r)
SG = 1.0 if np.dot(np.cross(n0, ring0[0] - c_r0), ring0[NAa // 2] - c_r0) > 0 else -1.0   # the rings' turning sense about the path
Z0 = np.vstack([ring0, ring0[:1]]); l0 = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Z0, axis=0), axis=1))]; FRAC = l0[:-1] / l0[-1]
def resample_closed(Y):
    Z = np.vstack([Y, Y[:1]]); l_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Z, axis=0), axis=1))]; t = FRAC * l_[-1]
    return np.array([np.interp(t, l_, Z[:, c]) for c in range(3)]).T
tube = []; holes = []
for k in range(1, ns - 1):
    # the cutting plane turns gradually from the junction ring's plane to the path's normal plane over the first BLEND m
    b = np.clip(ts[k] / BLEND, 0, 1); b = b * b * (3 - 2 * b); t_ = (1 - b) * n0 + b * tg[k]; t_ /= np.linalg.norm(t_)
    r = r - np.dot(r, t_) * t_; r /= np.linalg.norm(r); v = SG * np.cross(t_, r)
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
    dense = path[k] + np.cos(th)[:, None] * rad[:, None] * r + np.sin(th)[:, None] * rad[:, None] * v
    # the start point chosen so the ring lines up with the previous one point by point (no twist, no seam)
    prev = tube[-1] if tube else ring0; best_ = None
    for sh in range(0, NR, 4):
        cand = resample_closed(np.roll(dense, -sh, 0)); e = np.sum((cand - prev) ** 2)
        if best_ is None or e < best_[0]: best_ = (e, cand)
    tube.append(best_[1])
# one sequence: nacelle rings from the back to the front, then the tube
R0 = np.vstack([RN[::-1], np.array(tube)]); J = K - 1                       # J = the junction ring (front nacelle section)
def gs(y, sg, axis, wrap=False):
    k = np.exp(-0.5 * (np.arange(-3 * sg, 3 * sg + 1) / sg) ** 2); k /= k.sum()
    pad = (lambda z: np.pad(z, 3 * sg, mode="wrap")) if wrap else (lambda z: np.pad(z, 3 * sg, mode="edge"))
    return np.apply_along_axis(lambda z: np.convolve(pad(z), k, "valid"), axis, y)
def taubin(Y, axis, it, wrap=False):
    Y = np.moveaxis(Y.copy(), axis, 0)
    for _ in range(it):
        for f_ in (0.5, -0.53):
            if wrap: L = 0.5 * (np.roll(Y, 1, 0) + np.roll(Y, -1, 0)) - Y
            else: L = np.zeros_like(Y); L[1:-1] = 0.5 * (Y[:-2] + Y[2:]) - Y[1:-1]
            Y = Y + f_ * L
    return np.moveaxis(Y, 0, axis)
def twice(Y, sg, axis, wrap=False):                                         # gaussian twicing: smooth, barely shrinking
    g = gs(Y, sg, axis, wrap); gg = gs(g, sg, axis, wrap); return 2 * g - gg
RS = twice(twice(R0, 6, 1, True), 24, 0)
wz = np.exp(-((np.arange(len(R0)) - J) / 60.0) ** 2)[:, None, None]; wz[J:] = 1  # along the nacelle: the smoothing only near the junction
X = R0 * (1 - wz) + RS * wz
for k in range(J + 1):                                                      # the nacelle points exact, the arm curve's ends faded onto them
    nac = R0[k, NAa:]; X[k, NAa:] = nac; w = np.linspace(1, 0, NAa)[:, None]
    X[k, :NAa] += w * (R0[k, 0] - X[k, 0]) + w[::-1] * (R0[k, NAa - 1] - X[k, NAa - 1])
DJ = X[J] - RS[J]                                                           # what pinning moved at the junction ring...
for k in range(J + 1, len(X)): X[k] += DJ * np.exp(-(k - J) / 25.0)          # ...carried into the tube, fading, so no step
# the junction relaxed: along every point's path the rings J-W..J+W are relaxed (laplacian, many rounds) so the path bends
# smoothly through the junction; fixed: the window's ends, and up to J the nacelle points and the arm's two end points
W = 80; free = np.ones((2 * W + 1, NA), bool)
for q in range(W + 1): free[q, NAa:] = False; free[q, 0] = False; free[q, NAa - 1] = False
free[0] = False; free[-1] = False
Y = X[J - W:J + W + 1].copy()
for _ in range(5000):
    Yn = Y.copy(); Yn[1:-1] = 0.5 * Y[1:-1] + 0.25 * (Y[:-2] + Y[2:]); Y = np.where(free[:, :, None], Yn, Y)
X[J - W:J + W + 1] = Y
# past the junction the two lines where the arm met the nacelle's edges would run on as ridges over the tube: relaxed
# around the ring near those two places, fully at the junction, fading out over SEAM rings
SEAM = 60; idx_s = np.unique(np.concatenate([np.arange(NAa - 1 - 14, NAa + 14), np.arange(NA - 14, NA + 14) % NA])); idx_s = idx_s[(idx_s >= 0)]
for k in range(J + 1, min(J + SEAM, len(X) - 1)):
    f_ = 1 - (k - J) / SEAM; ring = X[k].copy()
    for _ in range(int(400 * f_)):
        rn = 0.5 * ring + 0.25 * (np.roll(ring, 1, 0) + np.roll(ring, -1, 0)); ring[idx_s] = rn[idx_s]
    X[k] = ring
Y = X[J - W:J + W + 1].copy()
for _ in range(2000):                                                      # and again along the paths, so the rings stay in step
    Yn = Y.copy(); Yn[1:-1] = 0.5 * Y[1:-1] + 0.25 * (Y[:-2] + Y[2:]); Y = np.where(free[:, :, None], Yn, Y)
X[J - W:J + W + 1] = Y
# toward the PS the arm runs on past the nacelle's end until the PS cuts it (BRAT_PS_M m): every point of the back ring
# continues along its own path, then the faces that end up inside the PS are removed (PS = R002 169_C, inside = behind
# its nearest vertex's normal), so the arm reaches the PS everywhere instead of stopping on the nacelle's last section
PSM = float(__import__("os").environ.get("BRAT_PS_M", "0")); NE = 0
if PSM > 0:
    stp = np.linalg.norm(X[0] - X[1], axis=1).mean(); NE = int(PSM / stp); dirs = X[0] - X[10]; dirs = gs(dirs, 6, 0, True); dirs /= np.linalg.norm(dirs, axis=1)[:, None]   # each point's direction, smoothed around the ring
    EXT = np.array([X[0] + dirs * stp * (i + 1) for i in range(NE)])
    X = np.vstack([EXT[::-1], X]); J += NE; OPN = np.vstack([OPN, np.repeat(OPN[-1:], NE, 0)]); K += NE
# or the arm ends in the plane of the nacelle's flat wide end (BRAT_CAPAT_PLAN = point, normal; arm frame): each path is
# cut where it first crosses the plane and the end rings are spread again at equal steps along their own path, from ring
# CAP_K to the plane, so the last ring lies in the plane and the oblique cut leaves no squashed faces
CAP = __import__("os").environ.get("BRAT_CAPAT_PLAN"); CAP_K = 60
if CAP:
    cp = np.array([float(v_) for v_ in CAP.split(",")]); cq, cn = cp[:3], cp[3:] / np.linalg.norm(cp[3:])
    for i in range(NA):
        pth = X[:CAP_K + 1, i][::-1]; d = (pth - cq) @ cn                     # from ring CAP_K out to ring 0
        k = int(np.argmax(d >= 0)); assert d[k] >= 0 and k > 0, "drumul %d nu ajunge la plan" % i
        e = pth[k - 1] + (pth[k] - pth[k - 1]) * (-d[k - 1] / (d[k] - d[k - 1]))
        pth = np.vstack([pth[:k], e]); s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pth, axis=0), axis=1))]
        u = np.linspace(0, s[-1], CAP_K + 1); X[:CAP_K + 1, i] = np.array([np.interp(u, s, pth[:, c]) for c in range(3)]).T[::-1]
    print("CAPAT IN PLAN: ultimul inel la %.4f m de plan (max), inelul %d fix" % (np.abs((X[0] - cq) @ cn).max(), CAP_K))
np.savez(OUT.replace(".blend", "_inele.npz"), X=X, R0=R0, J=J, NAa=NAa)
tipp = path[min(len(tube) + 1, ns - 1)]; L = len(X)
V = np.vstack([X.reshape(-1, 3), tipp[None]])
F = []
for k in range(L - 1):
    full = k >= J                                                           # along the nacelle only the arm part gets faces
    for i in (range(NA) if full else range(NAa - 1)):
        if not full and OPN[K - 1 - k, i:i + 2].any() and OPN[K - 2 - k, i:i + 2].any(): continue   # the funnel's open mouth (toward the PS)
        F.append((k * NA + i, k * NA + (i + 1) % NA, (k + 1) * NA + (i + 1) % NA, (k + 1) * NA + i))
F += [((L - 1) * NA + i, (L - 1) * NA + (i + 1) % NA, L * NA) for i in range(NA)]
mt = bpy.data.materials.get("brat_gri") or bpy.data.materials.new("brat_gri")
col = bpy.data.collections.get("BRAT_NOU") or bpy.data.collections.new("BRAT_NOU")
bk = bpy.data.collections.get("BRAT_PIESE") or bpy.data.collections.new("BRAT_PIESE")
if bk.name not in sc.collection.children: sc.collection.children.link(bk)
for o_ in list(col.objects): col.objects.unlink(o_); bk.objects.link(o_)
for s_ in (1, -1):
    W = V.copy(); W[:, 0] *= s_; me = bpy.data.meshes.new("brat_fata"); me.from_pydata((W + [DX, 0, 0]).tolist(), [], F if s_ > 0 else [f[::-1] for f in F]); me.materials.append(mt)
    for p_ in me.polygons: p_.use_smooth = True
    if PSM > 0 and not CAP:                                                 # faces inside the PS removed (only near the PS end)
        from mathutils import kdtree, Vector as V_
        ps = bpy.data.objects["R002 169_C"]; Mw = ps.matrix_world; Mn = Mw.to_3x3().inverted().transposed(); kd = kdtree.KDTree(len(ps.data.vertices))
        for i_, vv in enumerate(ps.data.vertices): kd.insert(Mw @ vv.co, i_)
        kd.balance(); pn = [(Mn @ vv.normal).normalized() for vv in ps.data.vertices]
        lim = (NE + 40) * NA; dele = []
        for p_ in me.polygons:
            if min(p_.vertices) >= lim: continue
            c_ = (sum((me.vertices[q].co for q in p_.vertices), V_()) / len(p_.vertices)) - V_((DX, 0, 0)); c_.x *= s_
            co, ix, dist = kd.find(c_)
            if (c_ - co).dot(pn[ix]) < -0.5: dele.append(p_.index)
        bt = bmesh.new(); bt.from_mesh(me); bt.faces.ensure_lookup_table(); bmesh.ops.delete(bt, geom=[bt.faces[i_] for i_ in dele], context="FACES"); bt.to_mesh(me); bt.free()
        print("PS: %d fete in interiorul PS scoase (%s)" % (len(dele), "_S" if s_ > 0 else "_D"))
        bt = bmesh.new(); bt.from_mesh(me); seen_, small = set(), []                # bits cut loose by the trim removed (islands < 200 faces)
        for f0 in bt.faces:
            if f0.index in seen_: continue
            st_, isl_ = [f0], []
            while st_:
                g_ = st_.pop()
                if g_.index in seen_: continue
                seen_.add(g_.index); isl_.append(g_); st_ += [h for e in g_.edges for h in e.link_faces if h.index not in seen_]
            if len(isl_) < 200: small += isl_
        bmesh.ops.delete(bt, geom=small, context="FACES"); bt.to_mesh(me); bt.free(); print("   bucati mici scoase: %d fete" % len(small))
    b2 = bmesh.new(); b2.from_mesh(me); bmesh.ops.remove_doubles(b2, verts=b2.verts, dist=0.001); bmesh.ops.delete(b2, geom=[v_ for v_ in b2.verts if not v_.link_faces], context="VERTS"); bmesh.ops.recalc_face_normals(b2, faces=b2.faces); b2.to_mesh(me)
    bnd = sum(1 for e in b2.edges if e.is_boundary); b2.free(); ob = bpy.data.objects.new("brat_fata%s" % ("_S" if s_ > 0 else "_D"), me); col.objects.link(ob)
    print("OBIECT %s: %d varfuri, %d fete, muchii libere %d (marginile pe nacela si spre corp)" % (ob.name, len(me.vertices), len(me.polygons), bnd))
bpy.context.view_layer.layer_collection.children["BRAT_PIESE"].exclude = True
arm = X[:, :NAa]; dj = np.gradient(X, axis=0); di = np.roll(X, -1, 1) - np.roll(X, 1, 1); nn = np.cross(di, dj); nn /= np.maximum(np.linalg.norm(nn, axis=2), 1e-9)[:, :, None]
turn = np.degrees(np.arccos(np.clip(np.sum(nn[1:] * nn[:-1], axis=2), -1, 1)))
jt = turn[max(J - 40, 0):J + 40]; ft = turn[J + 40:-5]
print("BRAT FATA: %d inele (%d pe nacela + %d tub, %.0f m pana la varf), %d puncte pe inel; rotire normala: la jonctiune max %.2f (p99 %.2f), pe tub max %.2f (p99 %.2f), pe nacela p99 %.2f"
      % (L, K, len(tube), l[-1], NA, jt.max(), np.percentile(jt, 99), ft.max(), np.percentile(ft, 99), np.percentile(turn[:J - 40, :NAa - 1], 99)))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
