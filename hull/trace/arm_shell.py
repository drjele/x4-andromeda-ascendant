# The front arm regenerated as one smooth continuous surface around the red nacelle (same lessons as the nacelle).
# In every nacelle cutting plane (its sections, perpendicular to the blue guide) the reference arm is a single surface
# that leaves the nacelle at one arm end (end1) and comes back to it at the other (end2), closing the loop. Construction:
#  * the reference arm (main mesh island only, no stray bits) cut by the plane -> points of its section;
#  * the arm's section = the curve from the nacelle's outer edge at end2 around to its outer edge at end1, taken as a
#    radius per angle around the loop's centre over the angles the nacelle does not cover, then resampled at equal arc length; angles where the reference has
#    a hole get the radius interpolated from both sides (the hole closed along the same curve);
#  * smoothed along the curve (gaussian) and along the row (gaussian over neighbouring sections), then its two ends set
#    exactly on the nacelle's outer edge points, so arm and nacelle meet flush with no gap;
#  * a single surface (like the reference arm), smooth, normals outward; one side, mirrored.
# Env: BRAT_PIESE = extra reference pieces (comma list), BRAT_RMAX = search radius around the nacelle section (m).
# Usage: blender -b <scene.blend> --python arm_shell.py -- <nacelle_sections.npy> <out.blend> <dx> <first> <last>
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; G = np.load(a[0]); OUT, DX, J0, J1 = a[1], float(a[2]), int(a[3]), int(a[4]); sc = bpy.context.scene
M = G.shape[1]; H = M // 2; NA = 160; NR = 480                           # NR raw angles, NA points by equal arc length
o = bpy.data.objects["brat_fata_022_S"]; bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
seen, best = set(), []
for f in bm.faces:                                                          # main island
    if f.index in seen: continue
    st, isl = [f], []
    while st:
        g = st.pop()
        if g.index in seen: continue
        seen.add(g.index); isl.append(g); st += [h for e in g.edges for h in e.link_faces if h.index not in seen]
    if len(isl) > len(best): best = isl
P = np.array([v.co for v in bm.verts]) - [DX, 0, 0]
T = np.array([[f.verts[0].index, f.verts[i].index, f.verts[i + 1].index] for f in best for i in range(1, len(f.verts) - 1)])
# toward the body the arm's loop is closed by other reference pieces (panels): their faces join the reference surface
EXTRA = [x for x in __import__("os").environ.get("BRAT_PIESE", "").split(",") if x]; RMAX_ = [float(x) for x in __import__("os").environ.get("BRAT_RMAX", "250").split(",")]   # "r" or "r0,r1,j0,j1": ramp over sections
RMAX_AT = lambda j: RMAX_[0] if len(RMAX_) == 1 else float(np.interp(j, [RMAX_[2], RMAX_[3]], RMAX_[:2]))
for nm in EXTRA:
    eo = bpy.data.objects[nm]; Me = np.array(eo.matrix_world); Ve = np.array([v.co for v in eo.data.vertices]) @ Me[:3, :3].T + Me[:3, 3]
    b0 = len(P); P = np.vstack([P, Ve]); T = np.vstack([T, np.array([[b0 + p_.vertices[0], b0 + p_.vertices[i], b0 + p_.vertices[i + 1]] for p_ in eo.data.polygons for i in range(1, len(p_.vertices) - 1)])])
def cut(o_, n):
    d = (P - o_) @ n; dd = d[T]; sel = (dd.min(1) < 0) & (dd.max(1) > 0); out = []
    for t, x in zip(T[sel], dd[sel]):
        for p_, q_ in ((0, 1), (1, 2), (2, 0)):
            if (x[p_] > 0) != (x[q_] > 0): w = x[p_] / (x[p_] - x[q_]); out.append(P[t[p_]] * (1 - w) + P[t[q_]] * w)
    return np.array(out).reshape(-1, 3)
# which outline point of the nacelle the arm leaves from, at each end: the one nearer the arm, by majority over the range
# (the same side on every section, otherwise the ends jump between the bar's two faces)
votes = [0, 0]
for j in range(J0, J1 + 1, 5):
    S = G[j]; c0 = S.mean(0); _, _, vt = np.linalg.svd(S - c0); Q = cut(c0, vt[2]); Q = Q[np.linalg.norm(Q - c0, axis=1) < RMAX_AT(j)]
    dq = lambda p_: np.min(np.linalg.norm(Q - p_, axis=1)); votes[0] += dq(S[0]) < dq(S[M - 1]); votes[1] += dq(S[H - 1]) < dq(S[H])
n_ = len(range(J0, J1 + 1, 5)); SIDE1 = 0 if votes[0] * 2 >= n_ else M - 1; SIDE2 = H - 1 if votes[1] * 2 >= n_ else H
# past the nacelle's end (BRAT_PRELUNG m): the arm runs on until the PS cuts it obliquely; extra sections = the last
# nacelle section moved forward along its normal (the nacelle points there are only a stand-in, they end up inside the PS)
PRE = float(__import__("os").environ.get("BRAT_PRELUNG", "0")); J1_NAC = J1
if PRE > 0:
    Sl = G[J1]; cl_ = Sl.mean(0); nl = np.linalg.svd(Sl - cl_)[2][2]; nl *= np.sign(np.dot(nl, cl_ - G[J1 - 20].mean(0)))
    step = np.linalg.norm(G[J1].mean(0) - G[J1 - 10].mean(0)) / 10; NE = int(PRE / step)
    G = np.vstack([G[:J1 + 1], np.array([Sl + nl * step * (i + 1) for i in range(NE)])]); J1 += NE
secs = []; HOLEF = []; GAPM = []
for j in range(J0, J1 + 1):
    S = G[j]; c0 = S.mean(0); _, _, vt = np.linalg.svd(S - c0); n = vt[2]; u = vt[0]; v = np.cross(n, u)
    Q = cut(c0, n); Q = Q[np.linalg.norm(Q - c0, axis=1) < RMAX_AT(j)]
    # outer edge points of the nacelle at end1 and end2: of each end's two outline points, the one nearer the arm
    e1 = S[SIDE1]; e2 = S[SIDE2]
    cen = np.vstack([Q, S]).mean(0); to2 = lambda X: np.stack([(X - cen) @ u, (X - cen) @ v], -1)
    q2, s2, a1, a2 = to2(Q), to2(S), to2(e1), to2(e2)
    ang = lambda X: np.arctan2(X[..., 1], X[..., 0])
    t1, t2, tn = ang(a1), ang(a2), ang(s2[H // 2])                         # tn: the nacelle's middle (its V point side)
    # the arm's angular interval: from end2 to end1 the way that does not pass the nacelle
    span = (t1 - t2) % (2 * np.pi); dirn = 1
    if ((tn - t2) % (2 * np.pi)) < span: span = 2 * np.pi - span; dirn = -1
    th = t2 + dirn * np.linspace(0, span, NR); rq = np.linalg.norm(q2, axis=1); aq = ang(q2); r = np.full(NR, np.nan)
    for i, t in enumerate(th):
        dt = np.abs((aq - t + np.pi) % (2 * np.pi) - np.pi); m = dt < span / NR * 2.5
        if m.sum(): r[i] = np.median(rq[m])
    r[0], r[-1] = np.linalg.norm(a2), np.linalg.norm(a1); ok = ~np.isnan(r); holes = int((~ok).sum())
    run = mx = 0; gse = (0, 0)
    for i in range(NR):                                                     # the longest stretch without surface, in metres
        run = run + 1 if not ok[i] else 0
        if run > mx: mx = run; gse = (i - run + 1, i + 1)
    GAPM.append(mx * span / NR * np.nanmedian(r))
    r = np.interp(np.arange(NR), np.where(ok)[0], r[ok])
    HOLEF.append(holes / NR)
    Yd = cen + np.cos(th)[:, None] * r[:, None] * u + np.sin(th)[:, None] * r[:, None] * v; ld = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Yd, axis=0), axis=1))]
    secs.append(dict(cen=cen, u=u, v=v, th=th, r=r, e1=e1, e2=e2, holes=holes, gap_m=GAPM[-1], Q=Q, gap_f=(ld[gse[0]] / ld[-1], ld[min(gse[1], NR - 1)] / ld[-1])))
# smoothing: along the curve, then along the row (same sample index = same relative angle), ends pinned on the nacelle
def gs(y, sg, axis=0):
    k = np.exp(-0.5 * (np.arange(-3 * sg, 3 * sg + 1) / sg) ** 2); k /= k.sum()
    return np.apply_along_axis(lambda z: np.convolve(np.pad(z, 3 * sg, mode="edge"), k, "valid"), axis, y)
def resample(Y):                                                          # equal arc length, so sample i is the same place on every section
    l = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Y, axis=0), axis=1))]; t = np.linspace(0, l[-1], NA); return np.array([np.interp(t, l, Y[:, c]) for c in range(3)]).T
X = np.array([resample(s_["cen"][None] + np.cos(s_["th"])[:, None] * s_["r"][:, None] * s_["u"] + np.sin(s_["th"])[:, None] * s_["r"][:, None] * s_["v"]) for s_ in secs])   # (sections, NA, 3)
def gsw(y, sg, axis):
    k = np.exp(-0.5 * (np.arange(-3 * sg, 3 * sg + 1) / sg) ** 2); k /= k.sum()
    return np.apply_along_axis(lambda z: np.convolve(np.pad(z, 3 * sg, mode="wrap"), k, "valid"), axis, y)
def taubin(Y, axis, it, wrap=False):
    # smoothing without shrinking (Taubin lambda/mu): the noise goes, the sharp outer edge of the arm stays where it is
    Y = np.moveaxis(Y.copy(), axis, 0)
    for _ in range(it):
        for f_ in (0.5, -0.53):
            if wrap: L = 0.5 * (np.roll(Y, 1, 0) + np.roll(Y, -1, 0)) - Y
            else: L = np.zeros_like(Y); L[1:-1] = 0.5 * (Y[:-2] + Y[2:]) - Y[1:-1]
            Y = Y + f_ * L
    return np.moveaxis(Y, 0, axis)
def twice(Y, sg, axis, wrap=False):
    # gaussian "twicing" (2G - GG): the noise is cut like a plain gaussian, but the shape is barely pulled in, so the
    # arm's sharp outer edge keeps its width (a plain gaussian narrowed it by 5-15 m)
    g = gs(Y, sg, axis) if not wrap else gsw(Y, sg, axis); gg = gs(g, sg, axis) if not wrap else gsw(g, sg, axis); return 2 * g - gg
X = twice(twice(X, 5, 1), 24, 0)
for k, s_ in enumerate(secs):                                               # ends exactly on the nacelle, the correction fading inward
    w = np.linspace(1, 0, NA)[:, None]; X[k] += w * (s_["e2"] - X[k, 0]) + w[::-1] * (s_["e1"] - X[k, -1])
# toward the PS the arm opens upward into a funnel whose rim joins the deck: from section OPEN_FROM on, the longest
# stretch without reference surface (if longer than OPEN_MIN m) stays open - no faces there - instead of being closed by
# a chord; its two ends smoothed along the row so the rim is a clean line
OPEN_FROM = int(__import__("os").environ.get("BRAT_DESCHIS", "100000")); OPEN_MIN = 20.0
OPEN = np.zeros((len(secs), NA), bool); ks = [k for k, s_ in enumerate(secs) if J0 + k >= OPEN_FROM and s_["gap_m"] >= OPEN_MIN]
if ks:
    f0 = np.array([secs[k]["gap_f"][0] for k in ks]); f1 = np.array([secs[k]["gap_f"][1] for k in ks])
    med = lambda y: np.array([np.median(y[max(0, i - 6):i + 7]) for i in range(len(y))]); f0, f1 = gs(med(f0), 3, 0), gs(med(f1), 3, 0)
    for k, a0, a1 in zip(ks, f0, f1): OPEN[k, int(round(a0 * (NA - 1))):int(round(a1 * (NA - 1))) + 1] = True
    print("PALNIE: deschisa pe sectiunile %d..%d (%d), gura intre %.0f%% si %.0f%% din curba" % (J0 + ks[0], J0 + ks[-1], len(ks), 100 * f0.mean(), 100 * f1.mean()))
if PRE > 0:                                                                 # past the nacelle: faces only where the reference arm is
    for k in range(J1_NAC + 1 - J0, len(secs)):
        Qk = secs[k]["Q"]
        if len(Qk) == 0: OPEN[k] = True; continue
        dmin = np.array([np.min(np.linalg.norm(Qk - x_, axis=1)) for x_ in X[k]]); pres = dmin < 4.0
        pres = np.convolve(pres.astype(float), np.ones(7) / 7, "same") > 0.5; OPEN[k] |= ~pres
    print("PRELUNGIRE: %d sectiuni dupa capatul nacelei (%.0f m), suprafata pastrata %.0f%% din ele" % (len(secs) - (J1_NAC + 1 - J0), PRE, 100 * (1 - OPEN[J1_NAC + 1 - J0:].mean())))
print("GOL MAXIM de la 360 (din 5 in 5, m):", [round(secs[k]["gap_m"]) for k in range(max(0, 360 - J0), len(secs), 5)])
np.savez(OUT.replace(".blend", "_dbg.npz"), X=X, Q=np.array([0]), G=G[J0:J1 + 1], OPEN=OPEN)
V = X.reshape(-1, 3); F = [(k * NA + i, k * NA + i + 1, (k + 1) * NA + i + 1, (k + 1) * NA + i) for k in range(len(secs) - 1) for i in range(NA - 1)]
mt = bpy.data.materials.get("brat_gri") or bpy.data.materials.new("brat_gri"); mt.diffuse_color = (0.6, 0.6, 0.62, 1)
col = bpy.data.collections.get("BRAT_NOU") or bpy.data.collections.new("BRAT_NOU")
if col.name not in sc.collection.children: sc.collection.children.link(col)
for side in (1, -1):
    W = V.copy(); W[:, 0] *= side; me = bpy.data.meshes.new("brat"); me.from_pydata((W + [DX, 0, 0]).tolist(), [], F if side > 0 else [f[::-1] for f in F])
    me.materials.append(mt)
    for p_ in me.polygons: p_.use_smooth = True
    bm2 = bmesh.new(); bm2.from_mesh(me); bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces); bm2.to_mesh(me); bm2.free()
    ob = bpy.data.objects.new("brat_nou%s" % ("_S" if side > 0 else "_D"), me); col.objects.link(ob)
for nm in ("brat_fata_022_S", "brat_fata_019_D"): bpy.data.objects[nm].hide_set(True); bpy.data.objects[nm].hide_render = True
gapn = max(max(np.linalg.norm(X[k, 0] - s_["e2"]), np.linalg.norm(X[k, -1] - s_["e1"])) for k, s_ in enumerate(secs))
turn = []
for k in range(1, len(secs) - 1):
    dj = X[k + 1] - X[k - 1]; di = np.gradient(X[k], axis=0); nn = np.cross(di, dj); turn.append(nn / np.linalg.norm(nn, axis=1)[:, None])
turn = np.array(turn); ang_ = np.degrees(np.arccos(np.clip(np.sum(turn[1:] * turn[:-1], axis=2), -1, 1)))
print("GOL MAXIM pe sectiune in m (din 5 in 5 de la %d):" % J0, np.round(GAPM[::5]).astype(int).tolist())
bk = np.where(ang_.max(1) > 3)[0]; print("   sectiuni cu rotire > 3 grade:", bk.tolist()[:60], len(bk), "din", len(ang_), "; mediana pe sectiune:", np.round(np.median(ang_, 1)[:30], 1).tolist())
print("BRAT: sectiuni %d..%d, %d puncte pe sectiune; goluri inchise in referinta (unghiuri fara suprafata): %d; capete pe nacela: abatere max %.3f m; rotire normala intre sectiuni max %.2f grade (p99 %.2f)"
      % (J0, J1, NA, sum(s_["holes"] for s_ in secs), gapn, ang_.max(), np.percentile(ang_, 99)))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
