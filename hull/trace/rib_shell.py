# The nacelle as one V-shaped band cut into ribs, so neighbouring ribs share the same contour and touch flush all round
# (no tile effect): the band's two faces span the yellow-blue and green-blue guides. Construction:
#  * cutting planes perpendicular to the blue guide at the current slot boundaries (rib_planes.py), each plane's corners =
#    the blue point and its cuts with the green and yellow guides;
#  * the cross-section profile: the copied ribs' bar (a curved V) measured in their own corner frame - per position u along
#    the V (u = a - b: -1 at end1, 0 at the point, +1 at end2) the centre line (a, b) and the bar's thickness - then
#    interpolated along the blue guide between the copied ribs (so it changes gradually) and smoothed;
#  * every plane's section = that profile placed on its 3 corners, as a closed outline (centre line +/- half thickness,
#    inside the plane); every rib = the solid between two consecutive sections, so ribs on both sides of a plane have the
#    identical section there. Copied slots dark red, generated light red. One side, mirrored; beside the reference.
# Usage: blender -b <completed.blend> --python rib_shell.py -- <aligned.json> <guides.json> <out.blend> <dx> <dy> [first last | gol K]
# "gol K": the slots from copied rib K to copied rib K+1 (both included), built in place (dy 0) of the ribs there, which are hidden;
# "toata": every slot, in place of all the old ribs (hidden), plus the tip; "toata uneste": also joined into one object per side.
# Smoothness: the profile (centre line and thickness) smoothed along the V (gaussian, the 3 corners kept exact) and along the
# row a cubic in the position on the blue guide fitted through the 29 copied ribs (no waves from rib to rib); SUB sections
# per rib; the normals computed on the whole band at once and set on every rib (no shading seams at the shared outlines).
import bpy, sys, json, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; CJ, GJ, OUT, DX, DY = a[0], a[1], a[2], float(a[3]), float(a[4])
GAP = int(a[6]) if len(a) > 6 and a[5] == "gol" else None; ALL = len(a) > 5 and a[5] == "toata"; SUB = 4; RANGE = (int(a[5]), int(a[6])) if len(a) > 6 and GAP is None and not ALL else None; R = json.load(open(CJ)); Gd = json.load(open(GJ)); sc = bpy.context.scene; N = len(R); NU = 81
def bez(c, t): c = np.array(c); t = np.atleast_1d(t)[:, None]; return (1 - t) ** 3 * c[0] + 3 * (1 - t) ** 2 * t * c[1] + 3 * (1 - t) * t ** 2 * c[2] + t ** 3 * c[3]
TS = np.linspace(-0.05, 1.2, 50001); GU = [bez(r["control"], TS) for r in Gd["rails"]]; TB = np.gradient(GU[1], axis=0); TB /= np.linalg.norm(TB, axis=1)[:, None]
def face(k, f): c = np.array(R[k][f]); return np.array([c[1], c[0], c[2]])     # (point, end1, end2)
def tpar(p): return int(np.argmin(np.linalg.norm(GU[1] - p, axis=1)))
# slots along the blue guide (same as rib_planes.py)
faces_pts, slots = [], []
for k in range(N):
    fb, ff = face(k, "spate"), face(k, "fata")
    if not faces_pts: faces_pts.append(fb[0])
    faces_pts.append(ff[0]); slots.append(True); copied_slot = locals().setdefault("copied_slot", []); copied_slot.append(len(slots) - 1)
    if k + 1 < N:
        F0, F1 = ff, face(k + 1, "spate"); width = np.linalg.norm(F1.mean(0) - F0.mean(0))
        rw = 0.5 * (np.linalg.norm(ff.mean(0) - fb.mean(0)) + np.linalg.norm(face(k + 1, "fata").mean(0) - F1.mean(0))); n = max(1, int(round(width / rw)))
        for j in range(n): f1 = (j + 1) / n; faces_pts.append((F0 * (1 - f1) + F1 * f1)[0]); slots.append(False)
# NACELA_EXTRA ribs added past the wide end (the one away from the guides' meeting point), each one rib wide, along the
# blue guide's own continuation, so the nacelle's head goes into the deck
EXTRA = int(__import__("os").environ.get("NACELA_EXTRA", "0"))
if EXTRA:
    apex_ = np.array(Gd["apex"]); wide_end = np.linalg.norm(faces_pts[-1] - apex_) > np.linalg.norm(faces_pts[0] - apex_)
    ends = faces_pts if wide_end else faces_pts[::-1]; rw_ = np.mean([np.linalg.norm(ends[-1 - j] - ends[-2 - j]) for j in range(3)])
    i0 = tpar(ends[-1]); step_ = 1 if wide_end else -1; new_ = []
    for e_ in range(EXTRA):
        acc = 0.0; i1 = i0
        while acc < rw_ and 0 < i1 + step_ < len(GU[1]): acc += np.linalg.norm(GU[1][i1 + step_] - GU[1][i1]); i1 += step_
        new_.append(GU[1][i1]); i0 = i1
    cs = [i for i, v in enumerate(slots) if v]; P_ = (cs[-1] - cs[-2]) if wide_end else (cs[1] - cs[0])   # the colour period (D l l)
    if wide_end:
        faces_pts += new_
        for e_ in range(EXTRA): slots.append(slots[len(slots) - P_])
    else:
        faces_pts = new_[::-1] + faces_pts
        for e_ in range(EXTRA): slots.insert(0, slots[P_ - 1]); copied_slot = [c + 1 for c in copied_slot]
    print("NACELA_EXTRA: %d nervuri adaugate la capatul lat (%s), latime nervura %.1f m, ghidaj pana la t %.3f" % (EXTRA, "final" if wide_end else "inceput", rw_, TS[i0]))
# NACELA_LATIME_EGALA: every rib the same width - the band's slot boundaries re-spaced at equal arc length along the blue
# guide, same count; the dark (copied-colour) ribs exactly every NACELA_PERIOADA ribs
if __import__("os").environ.get("NACELA_LATIME_EGALA"):
    i_a, i_b = tpar(faces_pts[0]), tpar(faces_pts[-1]); lo_, hi_ = min(i_a, i_b), max(i_a, i_b)
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(GU[1][lo_:hi_ + 1], axis=0), axis=1))]; ns_ = len(faces_pts)
    ii = lo_ + np.searchsorted(arc, np.linspace(0, arc[-1], ns_)).clip(0, hi_ - lo_)
    faces_pts = [GU[1][i] for i in (ii if i_a < i_b else ii[::-1])]; PER = int(__import__("os").environ.get("NACELA_PERIOADA", "4"))
    slots = [(i % PER) == 0 for i in range(ns_ - 1)]
    print("NACELA_LATIME_EGALA: %d nervuri de %.2f m, inchise din %d in %d (%d)" % (ns_ - 1, arc[-1] / (ns_ - 1), PER, PER, sum(slots)))
idx = np.array([tpar(p) for p in faces_pts])
def plane_corners(i):
    n = TB[i]; p = GU[1][i]; out = [p]
    for g in (GU[0], GU[2]):
        d = (g - p) @ n; j0 = int(np.argmin(np.linalg.norm(g - p, axis=1))); lo, hi = max(j0 - 8000, 0), min(j0 + 8000, len(g) - 1)
        ch = np.where(np.diff(np.sign(d[lo:hi])) != 0)[0]; jj = lo + ch[np.argmin(np.abs(lo + ch - j0))]; w = d[jj] / (d[jj] - d[jj + 1]); out.append(g[jj] * (1 - w) + g[jj + 1] * w)
    return np.array(out)
# the copied ribs' profile, measured along the bar: every vertex gets its position s along the rib from its geodesic
# distances (over the rib's edges) to the two arm ends, s = d1 / (d1 + d2), remapped so the point corner is at s = 0.5;
# per s sample the centre line = centroid of the vertices there (projected into the rib plane) written as (a, b) in the
# corner frame, and the thickness = their spread across the centre line inside the plane
import heapq
def geodesic(P, E, src):
    adj = [[] for _ in range(len(P))]
    for x, y in E: l = float(np.linalg.norm(P[x] - P[y])); adj[x].append((y, l)); adj[y].append((x, l))
    D = np.full(len(P), np.inf); D[src] = 0; h = [(0.0, src)]
    while h:
        d, v = heapq.heappop(h)
        if d > D[v]: continue
        for w, l in adj[v]:
            if d + l < D[w]: D[w] = d + l; heapq.heappush(h, (d + l, w))
    return D
S_ = np.linspace(0, 1, NU); prof = []; ppos = []; NOGEO = 0
for k in range(N):
    o = bpy.data.objects["nervura_copiata_%02d_S" % k]; P = np.array([o.matrix_world @ v.co for v in o.data.vertices]) - [DX, 0, 0]; E = [tuple(e.vertices) for e in o.data.edges]
    fb, ff = face(k, "spate"), face(k, "fata"); p, e1, e2 = (fb + ff) / 2; nrm = np.cross(e1 - p, e2 - p); nrm /= np.linalg.norm(nrm)
    Pp = P - np.outer((P - p) @ nrm, nrm); M = np.stack([e1 - p, e2 - p, nrm], 1)
    d1 = geodesic(P, E, int(np.argmin(np.linalg.norm(Pp - e1, axis=1)))); d2 = geodesic(P, E, int(np.argmin(np.linalg.norm(Pp - e2, axis=1))))
    ok = np.isfinite(d1) & np.isfinite(d2); NOGEO += int((~ok).sum()); sr = np.where(ok, d1 / np.maximum(d1 + d2, 1e-9), np.nan)
    sp = sr[int(np.argmin(np.where(ok, np.linalg.norm(Pp - p, axis=1), np.inf)))]
    s = np.where(sr < sp, 0.5 * sr / sp, 0.5 + 0.5 * (sr - sp) / (1 - sp))
    cl = np.zeros((NU, 2)); th = np.zeros(NU); C3 = np.zeros((NU, 3)); sels = []
    for i, ss in enumerate(S_):
        sel = np.where(ok & (np.abs(s - ss) < 0.6 / NU))[0]
        if len(sel) < 3: sel = np.argsort(np.where(ok, np.abs(s - ss), np.inf))[:6]
        C3[i] = Pp[sel].mean(0); sels.append(sel)
    C3[0], C3[NU // 2], C3[-1] = e1, p, e2                                  # the corners themselves
    cl = np.linalg.solve(M, (C3 - p).T).T[:, :2]; tg = np.roll(C3, -2, 0) - np.roll(C3, 2, 0)
    tg[:2] = C3[2:4] - C3[:2]; tg[-2:] = C3[-2:] - C3[-4:-2]; tg /= np.maximum(np.linalg.norm(tg, axis=1), 1e-9)[:, None]   # tangent over a wider step
    for i, sel in enumerate(sels):
        w = (Pp[sel] - C3[i]) @ np.cross(nrm, tg[i]); th[i] = max(np.percentile(w, 95) - np.percentile(w, 5), 0.3)
    bad = np.isnan(th) | (np.linalg.norm(tg, axis=1) < 0.5)
    if bad.any(): th[bad] = np.interp(np.where(bad)[0], np.where(~bad)[0], th[~bad])
    prof.append((cl, th)); ppos.append(tpar(p))
print("PROFIL: varfuri fara drum geodezic %d" % NOGEO)
ppos = np.array(ppos); X = (ppos - ppos[0]) / (ppos[-1] - ppos[0])
def gsmooth(y, sg):                                                        # gaussian along u, edges padded
    k = np.exp(-0.5 * (np.arange(-3 * sg, 3 * sg + 1) / sg) ** 2); k /= k.sum(); return np.convolve(np.pad(y, 3 * sg, mode="edge"), k, "valid")
CL = np.array([p_[0] for p_ in prof]); TH = np.array([p_[1] for p_ in prof]); ix = np.arange(NU); keys = [0, NU // 2, NU - 1]
for k in range(N):
    for c in range(2):
        y = gsmooth(CL[k, :, c], 4); CL[k, :, c] = y + np.interp(ix, keys, CL[k, keys, c] - y[keys])   # corners kept exact
    TH[k] = gsmooth(TH[k], 8)
PC = [np.polyfit(X, CL[:, :, c], 3) for c in range(2)]; PT = np.polyfit(X, TH, 3)   # cubic along the row, per u sample
def profile_at(i):
    x = (i - ppos[0]) / (ppos[-1] - ppos[0]); return np.stack([sum(PC[c][j] * x ** (3 - j) for j in range(4)) for c in range(2)], 1), sum(PT[j] * x ** (3 - j) for j in range(4))
def section(i):
    cl, th = profile_at(i); return section_from(plane_corners(i), TB[i], cl, th)
def section_from(pc, nv, cl, th):
    C = pc[0] + cl[:, :1] * (pc[1] - pc[0]) + cl[:, 1:2] * (pc[2] - pc[0]); tg = np.gradient(C, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]
    off = np.cross(nv, tg); off /= np.linalg.norm(off, axis=1)[:, None]
    return np.vstack([unfold(C + off * th[:, None] / 2, C), unfold(C - off * th[:, None] / 2, C)[::-1]])   # closed outline, in the plane
def unfold(Q, C):
    # at the V's tight point the inner offset can fold over itself (thickness > bend radius): there the offset curve is
    # relaxed (laplacian, the other points fixed) until it runs the same way as the centre line everywhere
    Q = Q.copy(); tc = np.gradient(C, axis=0)
    for _ in range(400):
        tq = np.gradient(Q, axis=0); bad = np.where(np.sum(tq * tc, axis=1) < 0.3 * np.linalg.norm(tq, axis=1) * np.linalg.norm(tc, axis=1))[0]
        if len(bad) == 0: break
        sel = np.unique(np.clip(np.concatenate([bad + d for d in range(-4, 5)]), 1, len(Q) - 2)); Q[sel] = 0.5 * Q[sel] + 0.25 * (Q[sel - 1] + Q[sel + 1])
    return Q
def mat(n_, c):
    m = bpy.data.materials.get(n_) or bpy.data.materials.new(n_); m.diffuse_color = c; m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = c; return m
RD = tuple(float(v) for v in __import__("os").environ.get("NACELA_ROSU", "0.35,0.03,0.04").split(",")) + (1,)
dark, light = mat("nervura_copiata_set", RD), mat("nervura_noua_rosu_deschis", (0.85, 0.12, 0.10, 1))
if __import__("os").environ.get("NACELA_UNIFORM"):                       # the copied ribs' colour spread evenly over the band
    nd = len(copied_slot) - sum(1 for c in copied_slot if c >= len(slots)); dk = set(np.round(np.linspace(0, len(slots) - 1, N)).astype(int))
    slots = [i in dk for i in range(len(slots))]; print("NACELA_UNIFORM: %d nervuri inchise din %d, la ~%.2f nervuri distanta" % (len(dk), len(slots), (len(slots) - 1) / (N - 1)))
col = bpy.data.collections.new("BANDA_V"); sc.collection.children.link(col)
lo_s, hi_s = RANGE if RANGE else (0, len(slots))
if GAP is not None: lo_s, hi_s = copied_slot[GAP], copied_slot[GAP + 1] + 1
for o in sc.objects:
    if (ALL and o.name.startswith(("nervura_copiata_", "nervura_noua_"))) or (GAP is not None and o.name.startswith(("nervura_copiata_%02d_" % GAP, "nervura_copiata_%02d_" % (GAP + 1), "nervura_noua_%02d_" % GAP))):
        o.hide_set(True); o.hide_render = True
# all sections of the range (SUB per rib, boundaries shared), then the normals of the whole band from the grid
pos = np.concatenate([np.linspace(idx[s_], idx[s_ + 1], SUB + 1)[:-1] for s_ in range(lo_s, hi_s)] + [[idx[hi_s]]])
G = np.array([section(int(round(q))) for q in pos]); M_ = G.shape[1]; NB = len(G)
# the tip ("toata"): from the band's end toward the meeting point of the 3 guides, along their extension curves (each moved
# at its start onto the band's end corner, the move fading as (1 - u)^2 so the meeting point stays); every section = the
# end profile placed on the 3 extension points at the same u, its thickness shrinking with the V's size, the last one the
# meeting point itself; as many ribs as fit at the real rib width, alternating dark and light
TIP = []; TIP_AT_START = False
if ALL:
    apex = np.array(Gd["apex"]); TIP_AT_START = np.linalg.norm(G[0].mean(0) - apex) < np.linalg.norm(G[-1].mean(0) - apex)
    ie = idx[lo_s] if TIP_AT_START else idx[hi_s]; pcE = plane_corners(ie); clE, thE = profile_at(ie); nE = TB[ie]
    ext = [np.array(r["extension_control"]) for r in Gd["rails"]]; RO = (1, 0, 2)          # pc order (point, end1, end2) -> rails
    E0 = np.array([bez(ext[r], 0.0)[0] for r in RO]); sizeE = np.linalg.norm(pcE[1] - pcE[0]) + np.linalg.norm(pcE[2] - pcE[0])
    us = np.linspace(0, 1, 400); blue = np.array([bez(ext[1], u)[0] + (1 - u) ** 2 * (pcE[0] - E0[0]) for u in us]); Lb = np.sum(np.linalg.norm(np.diff(blue, axis=0), axis=1))
    rw = np.median(np.linalg.norm(np.diff(np.array([GU[1][i] for i in idx]), axis=0), axis=1)); NT = max(2, int(round(Lb / rw))); NS = NT * SUB
    cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(blue, axis=0), axis=1))]                  # equal lengths along the blue guide
    for j in range(1, NS + 1):
        u = float(np.interp(j / NS * cum[-1], cum, us))
        if j == NS: TIP.append(np.repeat(apex[None], M_, 0)); continue
        pc = np.array([bez(ext[r], u)[0] + (1 - u) ** 2 * (pcE[i] - E0[i]) for i, r in enumerate(RO)])
        nv = np.cross(pc[1] - pc[0], pc[2] - pc[0]); nv /= np.linalg.norm(nv); nv *= np.sign(np.dot(nv, nE))
        sz = (np.linalg.norm(pc[1] - pc[0]) + np.linalg.norm(pc[2] - pc[0])) / sizeE; TIP.append(section_from(pc, nv, clE, thE * sz))
    TIP = np.array(TIP); G = np.vstack([TIP[::-1], G]) if TIP_AT_START else np.vstack([G, TIP])
OFF = len(TIP) if TIP_AT_START else 0
np.save(OUT.replace(".blend", "_sectiuni.npy"), G)
dj = np.gradient(G, axis=0); dm = np.roll(G, -1, axis=1) - np.roll(G, 1, axis=1); NRM = np.cross(dm, dj); nn = np.linalg.norm(NRM, axis=2)
NRM = np.where(nn[:, :, None] > 1e-9, NRM / np.maximum(nn, 1e-9)[:, :, None], 0)
cen = G.mean(1, keepdims=True); flip = np.sign(np.mean(np.sum(NRM * (G - cen), axis=2))); NRM *= flip   # outward
if ALL:                                                                     # at the meeting point: the direction of the tip
    ja = 0 if TIP_AT_START else len(G) - 1; jb = 1 if TIP_AT_START else len(G) - 2; d = G[ja].mean(0) - G[jb].mean(0); NRM[ja] = d / np.linalg.norm(d)
def build(js, name, mt, side):
    V = G[js].reshape(-1, 3).copy(); Nv = NRM[js].reshape(-1, 3).copy(); L = len(js)
    F = [(j * M_ + i, j * M_ + (i + 1) % M_, (j + 1) * M_ + (i + 1) % M_, (j + 1) * M_ + i) for j in range(L - 1) for i in range(M_)]
    if side < 0: V[:, 0] *= -1; Nv[:, 0] *= -1; F = [f[::-1] for f in F]
    me = bpy.data.meshes.new(name); me.from_pydata((V + [DX, DY, 0]).tolist(), [], F); me.materials.append(mt)
    for p_ in me.polygons: p_.use_smooth = True
    fn = np.array([p_.normal for p_ in me.polygons]); ok_ = [k for k in range(len(F)) if np.linalg.norm(fn[k]) > 0.5]
    if np.mean([np.dot(fn[k], Nv[F[k][0]]) for k in ok_]) < 0: me.flip_normals()
    me.normals_split_custom_set_from_vertices(Nv.tolist())
    ob = bpy.data.objects.new(name, me); col.objects.link(ob); return ob
for s_ in range(lo_s, hi_s):
    j0 = OFF + (s_ - lo_s) * SUB
    for side in (1, -1): build(list(range(j0, j0 + SUB + 1)), "banda_%03d%s" % (s_, "_S" if side > 0 else "_D"), dark if slots[s_] else light, side)
for t in range(len(TIP) // SUB):                                            # tip ribs, counted from the band's end outward
    j0 = (OFF - (t + 1) * SUB) if TIP_AT_START else (NB - 1 + t * SUB)
    for side in (1, -1): build(list(range(j0, j0 + SUB + 1)), "banda_varf_%02d%s" % (t, "_S" if side > 0 else "_D"), light if t % 2 == 0 else dark, side)
caps = [(OFF, "capat_spate"), (OFF + NB - 1, "capat_fata")]
if ALL: caps = [c for c in caps if c[0] != (OFF if TIP_AT_START else OFF + NB - 1)]
for j, nm in caps:                                                          # the open end(s) of the band (flat)
    H = M_ // 2; F = [(i + 1, i, M_ - 1 - i, M_ - 2 - i) for i in range(H - 1)]
    for side in (1, -1):
        V = G[j].copy(); V[:, 0] *= side; me = bpy.data.meshes.new(nm); me.from_pydata((V + [DX, DY, 0]).tolist(), [], F if side > 0 else [f[::-1] for f in F]); me.materials.append(dark)
        col.objects.link(bpy.data.objects.new("banda_%s%s" % (nm, "_S" if side > 0 else "_D"), me))
# checks: shared outlines between neighbours, and the smoothness along the row (angle between consecutive section normals)
gap = max(np.max(np.linalg.norm(np.array([v.co for v in bpy.data.objects["banda_%03d_S" % s_].data.vertices])[SUB * M_:] - np.array([v.co for v in bpy.data.objects["banda_%03d_S" % (s_ + 1)].data.vertices])[:M_], axis=1)) for s_ in range(lo_s, hi_s - 1))
inner = slice(1, len(G) - 2) if ALL else slice(0, len(G) - 1)               # the meeting point itself left out (one point)
turn = np.degrees(np.arccos(np.clip(np.sum(NRM[1:] * NRM[:-1], axis=2), -1, 1)))[inner]
print("BANDA V: %d nervuri (felii %d..%d) + %d la varf, %d sectiuni, %d puncte pe sectiune; contur comun intre vecine: abatere max %.3f m; grosime bara %.1f..%.1f m"
      % (hi_s - lo_s, lo_s, hi_s, len(TIP) // SUB, len(G), M_, gap, TH.min(), TH.max()))
if ALL: print("VARF: %.0f m pana la punctul de intalnire, %d nervuri; jonctiunea banda-varf: rotire normala %.2f grade" % (Lb, NT, turn[(OFF - 1 if TIP_AT_START else NB - 2) - 1].max()))
print("NETEZIME de-a lungul: rotire normala intre sectiuni consecutive max %.2f grade (p99 %.2f)" % (turn.max(), np.percentile(turn, 99)))
# "uneste": everything into one object per side; the pieces kept in BANDA_V_PIESE (hidden) for undo
if len(a) > 6 and a[6] == "uneste":
    import bmesh
    bk = bpy.data.collections.new("BANDA_V_PIESE"); sc.collection.children.link(bk)
    for sfx in ("_S", "_D"):
        parts = [o for o in col.objects if o.name.endswith(sfx) and "capat" not in o.name]; capsO = [o for o in col.objects if o.name.endswith(sfx) and "capat" in o.name]
        for o in parts + capsO: c_ = o.copy(); c_.data = o.data.copy(); bk.objects.link(c_); c_.name = "piesa_" + o.name
        me = bpy.data.meshes.new("nacela_rosie" + sfx); mats = []
        for o in parts + capsO:
            for m_ in o.data.materials:
                if m_ not in mats: mats.append(m_)
        for m_ in mats: me.materials.append(m_)
        Vs, Fs, Ms, Sm = [], [], [], []
        for o in parts + capsO:
            b0 = len(Vs); Vs += [tuple(v.co) for v in o.data.vertices]; mi = mats.index(o.data.materials[0])
            Fs += [tuple(b0 + x for x in p_.vertices) for p_ in o.data.polygons]; Ms += [mi] * len(o.data.polygons); Sm += [o not in capsO] * len(o.data.polygons)
        me.from_pydata(Vs, [], Fs); me.polygons.foreach_set("material_index", Ms); me.polygons.foreach_set("use_smooth", Sm)
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)   # welded, the end cap too (flat)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5); bm.to_mesh(me); bm.free(); me.validate()
        ob = bpy.data.objects.new("nacela_rosie" + sfx, me); sc.collection.objects.link(ob)
        for o in parts + capsO: bpy.data.objects.remove(o)
        bm = bmesh.new(); bm.from_mesh(me); bnd = sum(1 for e in bm.edges if e.is_boundary); nm_ = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary); bm.free()
        print("OBIECT %s: %d varfuri, %d fete, muchii libere (gauri) %d, nemanifold %d" % (ob.name, len(me.vertices), len(me.polygons), bnd, nm_))
    bpy.context.view_layer.layer_collection.children["BANDA_V_PIESE"].exclude = True
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
