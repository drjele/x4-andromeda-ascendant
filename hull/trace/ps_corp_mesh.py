# The PS body (169_C) as one continuous surface: the deck (envelope sections, ps_deck.py) from the nose back to YB, then
# a blend into the rear arm tube (ps_tube.py, round), then the tube to its open end. Each section is the half-loop of the
# deck (top from x = 0 out, bottom back, the wall at x = 0); every point of the deck's last half-loop gets the tube point
# at the same angle (around the half-loop's centre, in the tube's first frame), and the tube rings are evaluated at those
# same angles, so the deck, the blend and the tube share one point count and one order (no seam). The blend: cubic Hermite
# from the deck's last section (direction -y) to the tube's first ring (its own direction), then relaxed along the rows
# with both ends fixed; the U between the arms opens by itself. Other half mirrored; on the deck the two walls lie in
# x = 0, inside the solid - those faces removed, the halves welded. Built in ship coordinates (x + DX), moved by OFF.
# Usage: blender -b <file.blend> --python ps_corp_mesh.py -- <punte_corp.npz> <tub.npz> <out.blend> <dx> <off> [name]
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; DN, TN = np.load(a[0]), np.load(a[1]); OUT, DX = a[2], float(a[3]); OFF = Vector([float(v) for v in a[4].split(",")])
NAME = a[5] if len(a) > 5 else "comp_169_C"; YB = float(os.environ.get("CORP_YB", "-20")); TSTEP = int(os.environ.get("CORP_TUB_PAS", "2")); NI = 16
ys, s, E, X0, DEP, T, B = DN["ys"], DN["s"], DN["edge"], DN["x0"], DN["depth"], DN["top"], DN["bot"]; M = T.shape[1]
def half_loop(k):                                                       # _S half (x <= 0): top 0 -> edge, bottom edge -> 0, wall
    x = -(X0[k] + s * (E[k] - X0[k])); y = np.full(M, ys[k])
    top = np.stack([x, y, T[k]], 1); bot = np.stack([x, y, B[k]], 1)[::-1][1:]
    th = np.linspace(-np.pi / 2, np.pi / 2, NI + 2)[1:-1]; mid, hh = (T[k, 0] + B[k, 0]) / 2, (T[k, 0] - B[k, 0]) / 2
    wall = np.stack([-(X0[k] - DEP[k] * np.cos(th)), np.full(NI, ys[k]), mid + hh * np.sin(th)], 1)
    return np.vstack([top, bot, wall])
kd = [k for k in range(len(ys)) if ys[k] >= YB - 1e-6]; deck = np.array([half_loop(k) for k in kd])   # nose last
deck = deck[::-1]                                                       # order rows from the nose back to YB
TX, TC, TR = TN["X"], TN["C"], TN["R"]; NA = TR.shape[1]
e1 = (TX[:, 0] - TC) / TR[:, :1]; e2 = (TX[:, NA // 4] - TC) / TR[:, NA // 4:NA // 4 + 1]; tt = np.gradient(TC, axis=0); tt /= np.linalg.norm(tt, axis=1)[:, None]
D0 = deck[-1]; cD = D0.mean(0)
f1 = e1[0] * [1, 0, 1]; f1 /= np.linalg.norm(f1); f2 = e2[0] * [1, 0, 1]; f2 -= (f2 @ f1) * f1; f2 /= np.linalg.norm(f2)
th_i = np.unwrap(np.arctan2((D0 - cD) @ f2, (D0 - cD) @ f1))           # each deck point's angle (same handedness as the tube)
def ring_at(k):                                                         # tube ring k evaluated at the deck points' angles
    ang = np.linspace(0, 2 * np.pi, NA, endpoint=False); rr = np.interp(np.mod(th_i, 2 * np.pi), np.r_[ang, 2 * np.pi], np.r_[TR[k], TR[k, :1]])
    return TC[k] + rr[:, None] * (np.cos(th_i)[:, None] * e1[k] + np.sin(th_i)[:, None] * e2[k])
K0 = int(os.environ.get("CORP_TUB_K0", "0"))                            # the tube taken from ring K0: a longer blend
tube = np.array([ring_at(k) for k in range(K0, len(TC), TSTEP)])
T0 = tube[0]; Lb = np.linalg.norm(TC[K0] - cD); NB = max(int(Lb / 2.0), 4)
dD, dT = np.array([0, -1.0, 0]), tt[K0]
UW = float(os.environ.get("CORP_U", "0"))                               # > 0: the points near the middle open early -> a round U
wU = np.clip(1 - np.abs(D0[:, 0]) / 40.0, 0, 1)[:, None] * UW
blend = []
for j in range(1, NB):
    t0 = j / NB; tq = t0 + wU * (np.sin(np.pi * t0 / 2) ** 0.6 - t0)          # per point: eased parameter
    h00, h10, h01, h11 = 2 * tq ** 3 - 3 * tq ** 2 + 1, tq ** 3 - 2 * tq ** 2 + tq, -2 * tq ** 3 + 3 * tq ** 2, tq ** 3 - tq ** 2
    blend.append(h00 * D0 + h10 * Lb * dD + h01 * T0 + h11 * Lb * dT)
L = np.concatenate([deck, np.array(blend), tube]); n0 = len(deck) - 1; n1 = n0 + NB
# surface relaxation over the blend and EXT rows on each side (along the rows and around the ring), the outer 4 rows of
# the window fixed; the points lying in x = 0 on deck rows stay in x = 0 (the halves weld there): this rounds the U's apex
# and removes the creases where the blend meets the deck and the tube
EXT = int(os.environ.get("CORP_RELAX_EXT", "20")); a0, a1 = max(n0 - EXT, 0), min(n1 + EXT, len(L) - 1)
Y = L[a0:a1 + 1].copy(); onx = np.abs(Y[..., 0]) < 1e-6; fixed = np.zeros(len(Y), bool); fixed[:4] = fixed[-4:] = True
for _ in range(int(os.environ.get("CORP_RELAX", "400"))):
    Yn = Y.copy(); Yn[1:-1] = (2 * Y[1:-1] + Y[:-2] + Y[2:] + np.roll(Y[1:-1], 1, 1) + np.roll(Y[1:-1], -1, 1)) / 6
    Yn[fixed] = Y[fixed]; Yn[..., 0] = np.where(onx, 0.0, Yn[..., 0]); Y = Yn
L[a0:a1 + 1] = Y
PLD = os.environ.get("CORP_PLAN_D")                                    # plan-view warp to the flat guide (plan_field.py): x, y
if PLD:                                                                 # moved, z kept; the halves' wall stays on x = 0
    Dp = np.load(PLD)["d"]; assert Dp.shape == L[..., :2].shape, (Dp.shape, L.shape); onx = np.abs(L[..., 0]) < 1e-6
    L[..., :2] += Dp; L[..., 0] = np.where(onx, 0.0, np.minimum(L[..., 0], 0.0)); print("PLAN: deformare aplicata, max %.1f m" % np.abs(Dp).max())
SEC = os.environ.get("CORP_SECTIUNE")                                  # asked: the arms as thick everywhere as between the guides:
if SEC:                                                                 # every tube ring past YA gets the mean section of the rings
    YA_, YB_, YC_, YD_ = [float(v) for v in SEC.split(",")]            # centred in [YB_, YA_] (across x up, in the tube's own frame),
    n0_ = len(deck) + NB - 1; T_ = L[n0_:]; K_ = len(T_)                # ramped in over 60 rings; widened from the inner edge while the
    def g1(v, sg=4.0):                                                  # inner guide holds it (y > YC_, fading by YD_), else from the middle
        n = int(3 * sg); kk = np.exp(-0.5 * (np.arange(-n, n + 1) / sg) ** 2); kk /= kk.sum(); return np.convolve(np.pad(v, n, mode="edge"), kk, "valid")
    cen = np.stack([g1(T_.mean(1)[:, i]) for i in range(3)], 1); tg = np.gradient(cen, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]
    sd = np.cross(tg, [0, 0, 1.0]); ns = np.linalg.norm(sd, axis=1)
    for k in range(K_):
        if ns[k] < 0.2 and k: sd[k] = sd[k - 1]; ns[k] = 1.0
    sd /= ns[:, None]
    if sd[0, 0] < 0: sd[0] *= -1                                        # pointing to the middle (the _S half is at x < 0)
    for k in range(1, K_):
        if sd[k] @ sd[k - 1] < 0: sd[k] *= -1
    up = np.cross(sd, tg); up /= np.linalg.norm(up, axis=1)[:, None]
    A_ = np.einsum("kij,kj->ki", T_ - cen[:, None], sd); B_ = np.einsum("kij,kj->ki", T_ - cen[:, None], up)
    wl, hu = np.ptp(A_, axis=1), np.ptp(B_, axis=1); ref = (cen[:, 1] < YA_) & (cen[:, 1] > YB_)
    W_, H_ = float(np.median(wl[ref])), float(np.median(hu[ref])); k0 = int(np.nonzero(cen[:, 1] < YB_)[0][0])
    wr = np.clip((np.arange(K_) - k0) / 60.0, 0, 1); wr = wr * wr * (3 - 2 * wr)
    sa, sb = g1(1 + wr * (W_ / wl - 1), 6.0), g1(1 + wr * (H_ / hu - 1), 6.0)
    ui = np.clip((cen[:, 1] - YD_) / (YC_ - YD_), 0, 1); ui = ui * ui * (3 - 2 * ui)
    anc = ui * A_.max(1)                                                # the inner edge (towards the middle) or the middle
    T_ = cen[:, None] + ((anc[:, None] + (A_ - anc[:, None]) * sa[:, None]))[..., None] * sd[:, None] + (B_ * sb[:, None])[..., None] * up[:, None] \
        + (T_ - cen[:, None] - A_[..., None] * sd[:, None] - B_[..., None] * up[:, None])
    L[n0_:] = T_; L[..., 0] = np.minimum(L[..., 0], 0.0)
    print("SECTIUNE brate: %.1f x %.1f m (mediana inelelor intre y %.0f si %.0f), de la inelul %d; latime acum %.1f..%.1f" % (W_, H_, YB_, YA_, k0, (wl * sa).min(), (wl * sa).max()))
if os.environ.get("CORP_DUMP"): np.savez(os.environ["CORP_DUMP"], L=L, n_punte=len(deck), n_trecere=NB - 1); print("DUMP", L.shape); sys.exit(0)
LIN = os.environ.get("CORP_LINIE")                                      # asked: the outline seen from above = the round tip, then
if LIN:                                                                 # one straight line back to (XE, YE); applied after the
    XE, YE, RT, YT = [float(v) for v in LIN.split(",")]                 # relaxation, ring by ring (deck rows scaled in width, on the
    cy = YT - RT; Pp, Cc = np.array([XE, YE]), np.array([0.0, cy]); d_ = np.linalg.norm(Cc - Pp); be = np.arcsin(RT / d_); u0 = (Cc - Pp) / d_   # arm only
    tx, ty = max([Pp + np.array([[np.cos(b), -np.sin(b)], [np.sin(b), np.cos(b)]]) @ u0 * np.sqrt(d_ ** 2 - RT ** 2) for b in (be, -be)], key=lambda p: p[0])   # the outer side
    xline = lambda y: np.where(y <= ty, XE + (tx - XE) * (y - YE) / (ty - YE), np.sqrt(np.clip(RT ** 2 - (y - cy) ** 2, 0, None)))   # stretched), fading out
    FADE = 80.0                                                         # past YE
    for k in range(len(L)):
        ax = np.abs(L[k, :, 0]); io = int(np.argmax(ax)); yo = L[k, io, 1]; xo, xc = ax[io], ax.min()
        if xo - xc < 1e-6: continue
        w = np.clip((yo - (YE - FADE)) / FADE, 0, 1); tgt = (1 - w) * xo + w * float(xline(np.array(yo)))
        f_ = (tgt - xc) / (xo - xc); L[k, :, 0] = -(xc + (ax - xc) * f_)   # _S half: x <= 0
    print("CONTUR: varf rotund R %.0f, dreapta tangenta de la (%.0f, %.0f) la (%.0f, %.0f)" % (RT, tx, ty, XE, YE))
ULIN = os.environ.get("CORP_U_LINIE")                                   # asked: the arms' inner edges = ONE U line - an arc between the
if ULIN:                                                                # arms (its bottom at YA, flat there) and from it a straight
    XE2, YE2, RU2, YA = [float(v) for v in ULIN.split(",")]             # tangent line on each arm down to (XE2, YE2); applied ring by
    cy2 = YA - RU2; Pp, Cc = np.array([XE2, YE2]), np.array([0.0, cy2]); d_ = np.linalg.norm(Cc - Pp); be = np.arcsin(RU2 / d_); u0 = (Cc - Pp) / d_   # ring: only
    tx2, ty2 = max([Pp + np.array([[np.cos(b), -np.sin(b)], [np.sin(b), np.cos(b)]]) @ u0 * np.sqrt(d_ ** 2 - RU2 ** 2) for b in (be, -be)], key=lambda p: p[0])   # the inner side
    xin_line = lambda y: np.where(y <= ty2, XE2 + (tx2 - XE2) * (y - YE2) / (ty2 - YE2), np.sqrt(np.clip(RU2 ** 2 - (y - cy2) ** 2, 0, None)))   # moves, the outer
    for k in range(len(L)):                                             # side stays; fading out past YE2
        ax = np.abs(L[k, :, 0]); ii, io = int(np.argmin(ax)), int(np.argmax(ax)); yi, xi, xo = L[k, ii, 1], ax[ii], ax[io]
        if yi > YA or xo - xi < 1e-6: continue
        w = np.clip((yi - (YE2 - 80.0)) / 80.0, 0, 1); ti = (1 - w) * xi + w * float(xin_line(np.array(yi)))
        L[k, :, 0] = -(xo - (xo - ax) * (xo - ti) / (xo - xi))
    print("U: arc R %.0f cu fundul la y %.0f, drepte tangente de la (%.0f, %.0f) la (%.0f, %.0f)" % (RU2, YA, tx2, ty2, XE2, YE2))
K, N = L.shape[:2]; verts, faces = [], []
for side in (1, -1):
    V = L.copy(); V[..., 0] *= side; base = len(verts); verts += V.reshape(-1, 3).tolist()
    F = [(base + k * N + i, base + (k + 1) * N + i, base + (k + 1) * N + (i + 1) % N, base + k * N + (i + 1) % N) for k in range(K - 1) for i in range(N)]
    faces += F if side > 0 else [f[::-1] for f in F]
V = np.array(verts); V[:, 0] += DX
if NAME in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[NAME])
me = bpy.data.meshes.new(NAME); me.from_pydata(V.tolist(), [], faces)
bm = bmesh.new(); bm.from_mesh(me)
inner = [f for f in bm.faces if all(abs(v.co.x - DX) < 1e-4 for v in f.verts)]; bmesh.ops.delete(bm, geom=inner, context="FACES")
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01); bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.01)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS"); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bnd = sum(1 for e in bm.edges if e.is_boundary); nm = sum(1 for e in bm.edges if len(e.link_faces) > 2); bm.to_mesh(me); bm.free()
src = bpy.data.objects["R002 169_C"]; mi = src.data.polygons[0].material_index
for m_ in src.data.materials: me.materials.append(m_)
for p in me.polygons: p.use_smooth = True; p.material_index = mi
col = bpy.data.collections.get(os.environ.get("COLECTIE", "PS_NOU_EXPLODAT")) or bpy.data.collections.new(os.environ.get("COLECTIE", "PS_NOU_EXPLODAT"))
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
o = bpy.data.objects.new(NAME, me); col.objects.link(o); o.location = OFF
dr = np.linalg.norm(np.diff(L[n0 - 2:n1 + 3], axis=0), axis=2)
print("CORP %s: punte %d sectiuni, trecere %d (%.0f m), tub %d inele, %d puncte pe sectiune; %d varfuri, muchii libere %d (capetele tubului), nemanifold %d" % (NAME, len(deck), NB - 1, Lb, len(tube), N, len(me.vertices), bnd, nm))
for h in ("echiv_R002 169_C",):
    oo = bpy.data.objects.get(h)
    if oo:
        oo.hide_render = True
        try: oo.hide_set(True)
        except RuntimeError: pass                                       # in an excluded collection
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
