# Two sliding doors per front arm, one per blade group, each exactly as wide as its stowed blades (asked: two hatches the width
# of the blades, the middle strip between the two groups stays fixed, part of the arm). CLEAN= groups (default spate) get clean
# lines: door and arm cutout along one smooth curve with rounded corners (asked: clean lines on at_usa_spate_S and its cutout). Was: one sliding door instead of the flap (asked: like on aircraft - while the blades are in the arm, the piece of arm
# they come out through slides away forward / back like a sliding door, then the blades come out; and left / right must fold alike).
# Both workshop arms (at_/d_/s_brat_fata_S and _D: two meshes, each shared by the 3 instances, separate from the ship's) lose the
# same underside piece - downward-ish faces below the spine, from point 7 for S1 m along the spine, across -(FR+MG) x outer ...
# +(FR+MG) x inner half-width (D = the exact mirror) - which becomes the door <pre>usa_brat_S/D (TH m thick, inwards). The door moves
# along the arm, every point in the arm's own frame (spine point, across U, up N): first up into the arm by UP m, then slid towards
# the arm tip by L m (its across offset scaled to the arm's half-width there, so it stays inside); shape keys "etapa_k" (NS stages)
# keyed one after another = a path along the curve. The door keeps the arm's UVs and material (asked: same texture as the arm, so
# it can't be told apart) and has a round hole (column radius + CL) around each red column, which stays down through it.
# Timing in ATELIER_LAME (asked: once the blades are out, the hatch closes): 1 -> 1+FO opens (blades wait FO frames: lame_spirala.py
# FO=), FO+FD -> 2FO+FD closes behind the dropped blades, re-opens to be open at FO+2F-FD+1 when they climb back, 2F+FO -> 2F+2FO closes. Usage: blender -b <in.blend> --python lame_usa_culisanta.py -- <out.blend>
#   env FR=.6 MG=.25 S1=770 L=790 UP=7 TH=1.5 NS=16 FO=24 F=60 FD=20 SIG=20 CL=1
import bpy, bmesh, sys, os, json, math, numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
OUT = sys.argv[sys.argv.index("--") + 1]; E = lambda k, d: float(os.environ.get(k, d))
FR, MG, S1, L, UP, TH, NS, FO, F, SIG = E("FR", .6), E("MG", .25), int(E("S1", 770)), E("L", 790), E("UP", 7), E("TH", 1.5), int(E("NS", 16)), int(E("FO", 24)), int(E("F", 60)), E("SIG", 20)
FD, CL, MB, MBI = int(E("FD", 20)), E("CL", 1.0), E("MB", 3.0), int(E("MBI", 5))
CLEAN, SC, RC, MC = os.environ.get("CLEAN", "spate,fata").split(","), E("SC", 25), E("RC", 10), E("MC", 2)
XI = {"ATELIER_LAME": -7000.0, "ATELIER_DESCHISE": -9000.0, "ATELIER_STRANSE": -11000.0}; PRE = {"ATELIER_LAME": "at_", "ATELIER_DESCHISE": "d_", "ATELIER_STRANSE": "s_"}
g = bpy.data.objects["g_as_bf_sudat_S"]; LN = json.loads(g["linii"])
def line(nm):
    P = np.array([g.matrix_world @ p.co.xyz for p in g.data.splines[LN.index(nm)].points]) + [3100, 0, 0]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; u = np.arange(0, d[-1], 1.0); return np.c_[[np.interp(u, d, P[:, k]) for k in range(3)]].T
def gsm(A, sig):
    r = int(3 * sig); k = np.exp(-.5 * (np.arange(-r, r + 1) / sig) ** 2); k /= k.sum(); P = np.r_[2 * A[0] - A[r:0:-1], A, 2 * A[-1] - A[-2:-r - 2:-1]]
    return np.c_[[np.convolve(P[:, j], k, mode="valid") for j in range(A.shape[1])]].T
def kd(P):
    t = KDTree(len(P))
    for j, p in enumerate(P): t.insert(p, j)
    t.balance(); return t
Sp, Ci, Ce = line("g_as_bf_spinare_brat_fata_S"), line("g_as_bf_contur_interior_brat_fata_S"), line("g_as_bf_contur_exterior_brat_fata_S")
i0 = int(np.argmin(np.linalg.norm(Sp[:, :2] - [-59.6, 74.3], axis=1))); base = gsm(Sp[i0:], SIG); NB = len(base)
Tg = np.gradient(base, axis=0); Tg /= np.linalg.norm(Tg, axis=1)[:, None]; kc, ke = kd(Ci), kd(Ce)
U = np.array([np.array(kc.find(p)[0]) - p for p in base]); U -= Tg * (U * Tg).sum(1)[:, None]; U = gsm(U / np.linalg.norm(U, axis=1)[:, None], SIG); U /= np.linalg.norm(U, axis=1)[:, None]
N = np.cross(Tg, U); N /= np.linalg.norm(N, axis=1)[:, None]; N[N[:, 2] < 0] *= -1
hw = lambda t: gsm(np.array([np.linalg.norm((np.array(t.find(p)[0]) - p)[:2]) for p in base])[:, None], SIG)[:, 0]
HWI, HWO = hw(kc), hw(ke); kb = kd(np.c_[base[:, :2], np.zeros(NB)])
print("USA bratul de la 7 are %d m pe spinare; usa %d m, culisata %d m spre varf" % (NB, S1, L))
FR3 = int(E("FR3", 1)); kb3 = kd(base)
def frame(p):                                                            # ship point -> (i, t, l, n) in the arm frame
    if not FR3: _, i, _ = kb.find((p[0], p[1], 0)); d = np.array(p) - base[i]; return i, d @ Tg[i], d @ U[i], d @ N[i]
    p = np.array(p); _, i, _ = kb3.find(p)                               # FR3: foot of the perpendicular on the spine (|t| <= .5), so
    for _ in range(80):                                                  # frame(Pv(s, l, n)) = (s, l, n) and walls along N stay at one (s, l)
        st = int(round((p - base[i]) @ Tg[i])); st = max(-20, min(20, st))
        if st == 0 or not 0 <= i + st < NB: break
        i += st
    d = p - base[i]; return i, d @ Tg[i], d @ U[i], d @ N[i]
def place(i, t, l, n, ds, up):
    j = min(NB - 1, i + ds); h = (HWI[j] / HWI[i]) if l > 0 else (HWO[j] / HWO[i])
    return base[j] + Tg[j] * t + U[j] * l * h + N[j] * (n * DEP[j] / DEP[i] + up)
from mathutils.bvhtree import BVHTree as _B
_a = bpy.data.objects["at_brat_fata_S"].data; _t = _B.FromPolygons([v.co.copy() for v in _a.vertices], [list(p.vertices) for p in _a.polygons])
DEP = np.array([(_t.ray_cast(Vector(base[i]), Vector(-N[i]), 400)[3] or 30.0) for i in range(NB)]); DEP = gsm(DEP[:, None], SIG)[:, 0]
print("USA adancimea dedesubtului sub spinare: la 7 %.0f m, la 400 m %.0f m, la 800 m %.0f m, la 1500 m %.0f m" % (DEP[0], DEP[400], DEP[800], DEP[min(1500, NB - 1)]))
# --- footprint of each blade group (and its red column) swept while it drops out (frames 1+FO .. FO+FD), in the arm frame, kept only
# where it crosses the arm's underside (n above -DEP-5): per spine index the across range [lo, hi] (+MB margin)
GR = {}; obs = [o for o in bpy.data.collections["ATELIER_LAME"].objects if o.name.startswith(("at_lama_", "at_spinare_")) and o.name.endswith("_S")]
for fr in range(1 + FO, FO + FD + 2):
    bpy.context.scene.frame_set(fr); dg0 = bpy.context.evaluated_depsgraph_get()
    for o in obs:
        m = o.evaluated_get(dg0).to_mesh(); Q = [frame(tuple(o.matrix_world @ v.co - Vector((XI["ATELIER_LAME"], 0, 0)))) for v in m.vertices]; o.evaluated_get(dg0).to_mesh_clear()
        Q = [q for q in Q if q[3] > -DEP[q[0]] - 5]
        if not Q: continue
        gk = ("fata" if "fata" in o.name else "spate") if "spinare" in o.name else ("fata" if np.mean([q[2] for q in Q]) > 0 else "spate"); GR.setdefault(gk, []).extend(Q)
ENV = {}
for gk, Q in GR.items():
    I = np.array([q[0] for q in Q]); Lq = np.array([q[2] for q in Q]); ia, ib = I.min() - MBI, I.max() + MBI
    lo = np.full(NB, np.nan); hi = np.full(NB, np.nan)
    for i in range(I.min(), I.max() + 1):
        w = Lq[np.abs(I - i) <= 3]
        if len(w): lo[i], hi[i] = w.min(), w.max()
    ok = ~np.isnan(lo); x = np.arange(NB); lo = np.interp(x, x[ok], lo[ok]); hi = np.interp(x, x[ok], hi[ok])
    lo = -gsm(-lo[:, None], 4)[:, 0] - MB; hi = gsm(hi[:, None], 4)[:, 0] + MB
    ENV[gk] = (max(0, ia), min(NB - 1, ib), lo, hi)
    print("USA grup %s: %d lame-varfuri, pe spinare %d..%d m, latime %.0f..%.0f m (fara margine: %.0f..%.0f)" % (gk, len(Q), ia, ib, lo[I.min():I.max()].min(), hi[I.min():I.max()].max(), Lq.min(), Lq.max()))
# --- clean-line groups (CLEAN=): the outline is a smooth closed curve instead of the mesh's triangle edges - the across limits are
# smoothed upper / lower envelopes (gaussian SC m, never inside the swept blades), the ends straight across, corners rounded RC m;
# + MC m (the exact cut has no half-faces of slack); phi(p) < 0 inside (rounded-box distance in the arm frame); the arm skin is cut exactly along phi = 0 (edges split, faces split)
XS = np.arange(NB, dtype=float); CENV = {}
def envelope(h, sgn):
    g_ = h.copy()
    for _ in range(40): g_ = gsm((np.maximum(g_ * sgn, h * sgn) * sgn)[:, None], SC)[:, 0]
    return g_ + sgn * max(0.0, ((h - g_) * sgn).max())
for gk in CLEAN:
    if gk not in ENV: continue
    ia, ib, lo, hi = ENV[gk]; core = slice(ia + MBI, ib - MBI)
    los, his = envelope(lo, -1) - MC, envelope(hi, 1) + MC; CENV[gk] = (ia - RC - MC, ib + RC + MC, los, his)   # ends pushed out so the round corners never bite
    print("USA linii curate %s: lo %.1f..%.1f (era %.1f..%.1f), hi %.1f..%.1f; curbura max lo %.4f hi %.4f 1/m" % (gk, los[core].min(), los[core].max(), lo[core].min(), lo[core].max(), his[core].min(), his[core].max(), np.abs(np.diff(los, 2)).max(), np.abs(np.diff(his, 2)).max()))
def phi(p, gk):
    ia, ib, los, his = CENV[gk]; i, t, l, n = frame(p); s_ = min(max(i + t, 0), NB - 1); lo_, hi_ = np.interp(s_, XS, los), np.interp(s_, XS, his)
    qx, qy = max(lo_ - l, l - hi_) + RC, max(ia - (i + t), (i + t) - ib) + RC
    return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - RC
def cut_clean(bm, gk, mx, eps=.05):
    def und(f):
        c = f.calc_center_median(); return abs(f.normal.z) >= .2 and frame((c.x * mx, c.y, c.z))[3] <= 0
    U_ = [f for f in bm.faces if und(f)]; V_ = {v for f in U_ for v in f.verts}; PH = {v: phi((v.co.x * mx, v.co.y, v.co.z), gk) for v in V_}
    for v in V_:
        if abs(PH[v]) < eps: PH[v] = 0.0
    ed = {e for f in U_ for e in f.edges if PH[e.verts[0]] * PH[e.verts[1]] < 0}; zero = {v for v in V_ if PH[v] == 0.0}
    for e in ed:
        a, b = e.verts; fac = PH[a] / (PH[a] - PH[b]); ne, nv = bmesh.utils.edge_split(e, a, fac); PH[nv] = 0.0; zero.add(nv)
    U_ = [f for f in bm.faces if f.is_valid and all(v in PH for v in f.verts)]; ns = 0
    for f in U_:
        z = [v for v in f.verts if v in zero]
        if len(z) == 2 and not any(e for e in z[0].link_edges if z[1] in e.verts):
            bmesh.utils.face_split(f, z[0], z[1]); ns += 1
    bm.faces.index_update(); bm.normal_update()
    fs = [f for f in bm.faces if all(v in PH for v in f.verts) and max(PH[v] for v in f.verts) <= 0 and min(PH[v] for v in f.verts) < 0]
    print("USA linii curate %s: %d muchii taiate pe curba, %d fete impartite, %d fete in trapa" % (gk, len(ed), ns, len(fs))); return fs
# --- cut the two doors (one per blade group) out of both arms; the strip between the groups stays part of the arm
COMP = int(E("COMP", 1))
if not COMP:
    armS, armD = bpy.data.objects["at_brat_fata_S"], bpy.data.objects["at_brat_fata_D"]
    door = {}
    for sd, arm, mx in (("S", armS, 1), ("D", armD, -1)):
        me = arm.data; bm = bmesh.new(); bm.from_mesh(me); bm.faces.index_update(); sel = {gk: [] for gk in ENV}
        for gk in CENV: sel[gk] = cut_clean(bm, gk, mx)
        taken = {f for fs in sel.values() for f in fs}
        for f in bm.faces:
            if f in taken: continue
            if abs(f.normal.z) < .2: continue
            c = f.calc_center_median(); i, t, l, n = frame((c.x * mx, c.y, c.z))
            if n > 0: continue
            for gk, (ia, ib, lo, hi) in ENV.items():
                if gk in CENV: continue
                if ia <= i <= ib and lo[i] <= l <= hi[i]: sel[gk].append(f); break
        for gk, fs in sel.items():
            bd = bm.copy(); keep = {f.index for f in fs}; bd.faces.index_update()      # copy keeps the arm's UVs / material = same texture
            bmesh.ops.delete(bd, geom=[f for f in bd.faces if f.index not in keep], context="FACES")
            bmesh.ops.recalc_face_normals(bd, faces=bd.faces); r = bmesh.ops.extrude_face_region(bd, geom=bd.faces[:])
            for v in [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]: v.co.z += TH
            bmesh.ops.recalc_face_normals(bd, faces=bd.faces); dm = bpy.data.meshes.new("usa_%s_%s" % (gk, sd)); bd.to_mesh(dm); bd.free()
            for p in dm.polygons: p.use_smooth = True
            for m_ in me.materials: dm.materials.append(m_)
            # round hole for the group's red column (it stays down through the closed door while the blades are out): R = column + CL
            c = bpy.data.objects["at_spinare_%s_%s" % (gk, sd)]; cx, cy = c.matrix_world.translation.x - XI["ATELIER_LAME"], c.matrix_world.translation.y
            rc = max(v.co.xy.length for v in c.data.vertices) * c.scale.x + CL
            bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=rc, depth=1000, location=(cx, cy, 0)); cyl = bpy.context.active_object
            tmp = bpy.data.objects.new("tmp_gaura", dm); bpy.context.scene.collection.objects.link(tmp)
            mo = tmp.modifiers.new("g", "BOOLEAN"); mo.operation = "DIFFERENCE"; mo.object = cyl; mo.solver = "EXACT"
            dg = bpy.context.evaluated_depsgraph_get(); nm = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
            n0 = len(dm.vertices); dm.clear_geometry(); bmn = bmesh.new(); bmn.from_mesh(nm); bmn.to_mesh(dm); bmn.free(); bpy.data.meshes.remove(nm)
            bpy.data.objects.remove(tmp); bpy.data.objects.remove(cyl)
            door[gk + "_" + sd] = (dm, mx); print("USA %s %s: %d fete scoase, gaura R %.1f m la coloana (%.1f, %.1f), usa %d -> %d varfuri" % (gk, sd, len(fs), rc, cx, cy, n0, len(dm.vertices)))
        bmesh.ops.delete(bm, geom=[f for fs in sel.values() for f in fs], context="FACES"); bm.to_mesh(me); bm.free(); me.update()
# --- COMP=1 (asked: each blade set in its own compartment inside the arm, nothing of the arm's inside visible with the hatch open,
# no surface through another): per group, in the arm frame (s, l, n), solids over the clean outline (rounded box phi = offset):
#   hole  B0 phi < 0      from the skin - 3 to the skin + EPS + .3  -> the cutout in the skin, a rim EPS thick around it
#   door  Bd phi < -DSEAM  -> the door = the arm skin inside it (seam DSEAM all round), thickened TH along N
#   bay   Bg phi < GAP    from the skin + EPS to n = CEIL           -> the compartment (walls GAP off the door, ceiling over the blades)
#   tube  the door's whole slide (raised UP, slid 0..L, in the arm's normalised frame) + GT -> the pocket the door slides into
# bay + tube are clipped by the other hull pieces they cross (PS, carena, ears ...: they end on those surfaces), the arm loses
# hole + bay + tube (exact boolean); S built, D = the exact mirror. Env GAP=.5 EPS=.5 DSEAM=.15 GT=.4 CEIL=17
if COMP:
    from mathutils.bvhtree import BVHTree as BV
    GAP, EPS, DSEAM, GT, CEIL = E("GAP", .5), E("EPS", .5), E("DSEAM", .15), E("GT", .4), E("CEIL", 17)
    armS, armD = bpy.data.objects["at_brat_fata_S"], bpy.data.objects["at_brat_fata_D"]; meS = armS.data
    tA = BV.FromPolygons([v.co.copy() for v in meS.vertices], [list(p.vertices) for p in meS.polygons])
    def Pv(s, l, n):
        i = np.clip(np.rint(s).astype(int), 0, NB - 1); t = s - i
        return base[i] + Tg[i] * t[..., None] + U[i] * l[..., None] + N[i] * n[..., None]
    def skin(S_, L_):                                                    # n of the arm underside below (s, l); misses (past the arm end) filled
        O = Pv(S_, L_, np.zeros_like(S_)); i = np.clip(np.rint(S_).astype(int), 0, NB - 1); out = np.full(S_.shape, np.nan)
        for ix in np.ndindex(S_.shape):
            h = tA.ray_cast(Vector(O[ix]), Vector(-N[i[ix]]), 200)
            if h[0] is not None: out[ix] = -h[3]
        for k in range(S_.shape[1]):
            c = out[:, k]; ok = ~np.isnan(c)
            out[:, k] = np.interp(np.arange(len(c)), np.where(ok)[0], c[ok]) if ok.any() else -DEP[i[:, k]]
        return out
    def outline(gk, g):                                                  # phi = g as per-s intervals [a, b]; dense rows on the round ends
        ia, ib, los, his = CENV[gk]; e = RC + g; s0, s1 = ia - g, ib + g; c = 1 - np.cos(np.linspace(0, np.pi / 2, 24))
        S_ = np.unique(np.round(np.r_[s0 + e * c, np.arange(s0 + e, s1 - e, 1.0), s1 - e * c], 4))
        lo, hi = np.interp(np.clip(S_, 0, NB - 1), XS, los), np.interp(np.clip(S_, 0, NB - 1), XS, his)
        qy = np.maximum(ia - S_, S_ - ib) + RC; w = RC - np.sqrt(np.maximum(e ** 2 - np.maximum(qy, 0) ** 2, 0)); return S_, lo + w, hi - w
    def slab(name, Sg, Lg, Fn, Tn):                                      # closed solid: rows along s, columns across, floor Fn / top Tn (n)
        R, K1 = Sg.shape; Vb, Vt = Pv(Sg, Lg, Fn).reshape(-1, 3), Pv(Sg, Lg, Tn).reshape(-1, 3); nb = R * K1; ix = lambda r, k, top: top * nb + r * K1 + k
        fs = []
        for r in range(R - 1):
            for k in range(K1 - 1): fs += [(ix(r, k, 0), ix(r + 1, k, 0), ix(r + 1, k + 1, 0), ix(r, k + 1, 0)), (ix(r, k, 1), ix(r, k + 1, 1), ix(r + 1, k + 1, 1), ix(r + 1, k, 1))]
            fs += [(ix(r, 0, 0), ix(r, 0, 1), ix(r + 1, 0, 1), ix(r + 1, 0, 0)), (ix(r, K1 - 1, 0), ix(r + 1, K1 - 1, 0), ix(r + 1, K1 - 1, 1), ix(r, K1 - 1, 1))]
        for r in (0, R - 1):
            for k in range(K1 - 1): fs.append((ix(r, k, 0), ix(r, k + 1, 0), ix(r, k + 1, 1), ix(r, k, 1)))
        me = bpy.data.meshes.new(name); me.from_pydata(np.r_[Vb, Vt].tolist(), [], fs); me.validate()
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.matrix_world = armS.matrix_world.copy(); return o
    def box(name, gk, g, f_lo, f_hi, K=24):
        S_, A, B = outline(gk, g); Lg = A[:, None] + (B - A)[:, None] * np.linspace(0, 1, K + 1)[None]; Sg = np.repeat(S_[:, None], K + 1, 1); sk = skin(Sg, Lg)
        return slab(name, Sg, Lg, f_lo(sk), f_hi(sk))
    def boolean(obj, op, operand, hole=False):
        m = obj.modifiers.new("b", "BOOLEAN"); m.operation = op; m.solver = "EXACT"; m.use_self = False; m.use_hole_tolerant = hole
        if isinstance(operand, bpy.types.Collection): m.operand_type = "COLLECTION"; m.collection = operand
        else: m.object = operand
        dg = bpy.context.evaluated_depsgraph_get(); nm = bpy.data.meshes.new_from_object(obj.evaluated_get(dg)); obj.modifiers.remove(m); return nm
    def on_arm(p, tol=2e-3):
        r = tA.find_nearest(p); return r[0] is not None and r[3] < tol
    def tube(name, gk, Vd):                                              # pocket of the sliding door: in (s, u = l / half-width, nu = n / depth)
        Q = np.array([frame(tuple(p)) for p in Vd]); i = Q[:, 0].astype(int); s = i + Q[:, 1]; l, n = Q[:, 2], Q[:, 3]
        HW = HWI if l.mean() > 0 else HWO; u, nu = l / HW[i], n / DEP[i]; DS_, NU = 2.0, 40
        s0 = s.min(); nbn = int((s.max() - s0) / DS_) + 1; ub = np.linspace(u.min(), u.max(), NU + 1); uc = (ub[:-1] + ub[1:]) / 2
        bi = ((s - s0) / DS_).astype(int); bu = np.clip(np.searchsorted(ub, u) - 1, 0, NU - 1)
        mn = np.full((nbn, NU), np.inf); mxx = np.full((nbn, NU), -np.inf); np.minimum.at(mn, (bi, bu), nu); np.maximum.at(mxx, (bi, bu), nu)
        um = np.full(nbn, np.inf); uM = np.full(nbn, -np.inf); np.minimum.at(um, bi, u); np.maximum.at(uM, bi, u)
        nt = int((s.max() + L + GT + 2 - s0) / DS_) + 1; ST = s0 + DS_ * np.arange(nt); w = int(L / DS_); K = 24   # end past the door tip + GT
        Sg = np.repeat(ST[:, None], K + 1, 1); Lg = np.zeros_like(Sg); Fn = np.zeros_like(Sg); Tn = np.zeros_like(Sg)
        for k in range(nt):
            a, b = min(max(0, k - w), nbn - 1), min(nbn, k + 1); lo_, hi_ = mn[a:b].min(0), mxx[a:b].max(0); ok = np.isfinite(lo_)
            lo_ = np.minimum.reduce([np.roll(lo_, d) for d in (-1, 0, 1)]); hi_ = np.maximum.reduce([np.roll(hi_, d) for d in (-1, 0, 1)])
            lo_[~np.isfinite(lo_)] = np.nan; hi_[~np.isfinite(hi_)] = np.nan; ok = ~np.isnan(lo_) & ~np.isnan(hi_)
            sc_ = min(max(ST[k], 0), NB - 1); hw_, dep_ = np.interp(sc_, XS, HW), np.interp(sc_, XS, DEP)
            uk = np.linspace(um[a:b].min() - GT / hw_, uM[a:b].max() + GT / hw_, K + 1)
            Lg[k] = uk * hw_; Fn[k] = np.interp(uk, uc[ok], lo_[ok]) * dep_ + UP - GT; Tn[k] = np.interp(uk, uc[ok], hi_[ok]) * dep_ + UP + GT
        sk = skin(Sg, Lg); low = Fn < sk + .3; Fn = np.maximum(Fn, sk + .3); Tn = np.maximum(Tn, Fn + .5)   # floor never through the arm skin
        print("USA COMP tub %s: s %.0f..%.0f, n %.1f..%.1f; podea ridicata peste piele in %d puncte" % (gk, ST[0], ST[-1], Fn.min(), Tn.max(), low.sum())); return slab(name, Sg, Lg, Fn, Tn)
    HOSTS = [o for o in bpy.data.collections["ATELIER_LAME"].objects if o.type == "MESH" and not o.name.startswith(("at_lama_", "at_spinare_", "at_usa_", "at_brat_fata_")) and not o.name.endswith("_D")]
    def bvo(o):
        dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); m = oe.to_mesh(); r = BV.FromPolygons([o.matrix_world @ v.co for v in m.vertices], [list(p.vertices) for p in m.polygons]); oe.to_mesh_clear(); return r
    bpy.context.scene.frame_set(1); BH = {o.name: bvo(o) for o in HOSTS}
    cut_col = bpy.data.collections.new("tmp_taieturi"); bpy.context.scene.collection.children.link(cut_col); doorS = {}; HIT = set(); BGS = []
    for gk in CENV:
        Bd = box("tmp_Bd_" + gk, gk, -DSEAM, lambda sk: sk - 3, lambda sk: sk + 2)
        nm = boolean(armS, "INTERSECT", Bd, hole=True); bpy.data.objects.remove(Bd)
        bd = bmesh.new(); bd.from_mesh(nm); bpy.data.meshes.remove(nm)
        bmesh.ops.delete(bd, geom=[f for f in bd.faces if not (on_arm(f.calc_center_median()) and all(on_arm(v.co) for v in f.verts))], context="FACES")
        bmesh.ops.delete(bd, geom=[v for v in bd.verts if not v.link_faces], context="VERTS")
        bmesh.ops.recalc_face_normals(bd, faces=bd.faces); r = bmesh.ops.extrude_face_region(bd, geom=bd.faces[:])
        for v in [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]: v.co += Vector(N[frame(tuple(v.co))[0]]) * TH
        bmesh.ops.recalc_face_normals(bd, faces=bd.faces); dm = bpy.data.meshes.new("usa_%s_S" % gk); bd.to_mesh(dm); bd.free()
        for p in dm.polygons: p.use_smooth = True
        for m_ in meS.materials: dm.materials.append(m_)
        c = bpy.data.objects["at_spinare_%s_S" % gk]; cx, cy = c.matrix_world.translation.x - XI["ATELIER_LAME"], c.matrix_world.translation.y
        rc = max(v.co.xy.length for v in c.data.vertices) * c.scale.x + CL
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=rc, depth=1000, location=(cx, cy, 0)); cyl = bpy.context.active_object
        tmp = bpy.data.objects.new("tmp_gaura", dm); bpy.context.scene.collection.objects.link(tmp)
        nm = boolean(tmp, "DIFFERENCE", cyl); dm.clear_geometry(); bmn = bmesh.new(); bmn.from_mesh(nm); bmn.to_mesh(dm); bmn.free(); bpy.data.meshes.remove(nm)
        bpy.data.objects.remove(tmp); bpy.data.objects.remove(cyl); doorS[gk] = dm
        print("USA COMP usa %s: %d fete (piele + grosime %.1f m pe N), gaura R %.1f m" % (gk, len(dm.polygons), TH, rc))
        B0 = box("tmp_B0_" + gk, gk, 0.0, lambda sk: sk - 3, lambda sk: sk + EPS + .3)
        Bg = box("tmp_Bg_" + gk, gk, GAP, lambda sk: sk + EPS, lambda sk: np.full_like(sk, CEIL))
        Tb = tube("tmp_T_" + gk, gk, [v.co.copy() for v in dm.vertices])
        nm = boolean(Bg, "UNION", Tb); Bg.data = nm; bpy.data.objects.remove(Tb)
        tb = bvo(Bg); hit = [o for o in HOSTS if tb.overlap(BH[o.name])]; HIT.update(o.name for o in hit); BGS.append(Bg)
        print("USA COMP %s: golas + tub intra in %s" % (gk, ", ".join(o.name[3:] for o in hit) or "nimic"))
        for o in (B0, Bg): bpy.context.scene.collection.objects.unlink(o); cut_col.objects.link(o)
    def loops_free(me):
        bm = bmesh.new(); bm.from_mesh(me); fe = [e for e in bm.edges if e.is_boundary]; seen = set(); nl = 0
        for e0 in fe:
            if e0 in seen: continue
            nl += 1; st = [e0]
            while st:
                e = st.pop()
                if e in seen: continue
                seen.add(e); st += [x for v in e.verts for x in v.link_edges if x.is_boundary and x not in seen]
        n_ = len(fe); bm.free(); return n_, nl
    f0 = loops_free(meS); BGM = [o.data.copy() for o in BGS]
    # the arm is open at the nacelle mouth: capped for the boolean (else nothing counts as inside it), faces tagged arm 1 / cap 2 /
    # new 0, the cap removed again afterwards
    bc = bmesh.new(); bc.from_mesh(meS); src = bc.faces.layers.int.new("src")
    for f in bc.faces: f[src] = 1
    cap = bmesh.ops.holes_fill(bc, edges=[e for e in bc.edges if e.is_boundary], sides=0)["faces"]
    for f in cap: f[src] = 2
    flip = bc.calc_volume(signed=True) < 0                              # the arm's normals point inwards: flipped for the boolean, back after
    if flip: bmesh.ops.reverse_faces(bc, faces=bc.faces[:])
    capm = bpy.data.meshes.new("tmp_brat_inchis"); bc.to_mesh(capm); bc.free()
    for m_ in meS.materials: capm.materials.append(m_)
    tmpA = bpy.data.objects.new("tmp_brat_inchis", capm); bpy.context.scene.collection.objects.link(tmpA); tmpA.matrix_world = armS.matrix_world.copy()
    nm = boolean(tmpA, "DIFFERENCE", cut_col); bpy.data.objects.remove(tmpA); bpy.data.meshes.remove(capm)
    if not int(E("KEEPCUT", 0)):
        for o in list(cut_col.objects): bpy.data.objects.remove(o)
        bpy.data.collections.remove(cut_col)
    bm = bmesh.new(); bm.from_mesh(nm); bpy.data.meshes.remove(nm); uvl = bm.loops.layers.uv.active; cav = []; src = bm.faces.layers.int.get("src")
    if flip: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[src] == 2], context="FACES"); bm.faces.layers.int.remove(src)
    for f in bm.faces:
        if not on_arm(f.calc_center_median()):
            cav.append(f); f.material_index = 0
            if uvl:
                for lp in f.loops: lp[uvl].uv = (lp.vert.co.x / 256.0, lp.vert.co.y / 256.0)
    cs = set(cav)
    for f in cav: f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2 and any(f in cs for f in e.link_faces) and e.calc_face_angle(0) > math.radians(30): e.smooth = False
    bm.to_mesh(meS); bm.free(); meS.update(); f1 = loops_free(meS)
    print("USA COMP brat S: %d fete noi (compartimente); muchii libere %d in %d bucle -> %d in %d bucle" % (len(cav), f0[0], f0[1], f1[0], f1[1]))
    def mirror_into(src, dst):
        bm = bmesh.new(); bm.from_mesh(src)
        for v in bm.verts: v.co.x = -v.co.x
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); dst.clear_geometry(); bm.to_mesh(dst); bm.free(); dst.update()
    # the other hull pieces the compartments run into (PS, carena, ears, frame): their surface inside a compartment is cut out exactly on
    # its walls (no copies, nothing crossing the blades); new walls only where a compartment leaves the arm (inside that piece)
    bc = bmesh.new(); bc.from_mesh(meS); bmesh.ops.holes_fill(bc, edges=[e for e in bc.edges if e.is_boundary], sides=0)
    tArm = BV.FromBMesh(bc); bc.free(); DIRS = [Vector((.0123, .0071, 1)).normalized(), Vector((.61, -.33, .72)).normalized()]
    def inside_arm(p):                                                   # ray parity (two directions agree) on the arm closed at its mouth
        votes = 0
        for d in DIRS:
            o_, k = Vector(p), 0
            for _ in range(200):
                h = tArm.ray_cast(o_, d, 5000)
                if h[0] is None: break
                k += 1; o_ = h[0] + d * 1e-3
            votes += k % 2
        return votes == 2
    cutH = bpy.data.collections.new("tmp_gol_gazde"); bpy.context.scene.collection.children.link(cutH)
    for k_, m0 in enumerate(BGM):
        for side in (1, -1):
            mm = m0.copy()
            if side < 0:
                bm = bmesh.new(); bm.from_mesh(mm)
                for v in bm.verts: v.co.x = -v.co.x
                bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(mm); bm.free()
            o = bpy.data.objects.new("tmp_gol_%d_%d" % (k_, side), mm); cutH.objects.link(o); o.matrix_world = armS.matrix_world.copy()
    hosts = sorted(HIT)                                                  # _S pieces carved; their _D twins = the exact mirror (below)
    for hn in hosts:
        h = bpy.data.objects[hn]; hm = h.data; tH = BV.FromPolygons([v.co.copy() for v in hm.vertices], [list(p.vertices) for p in hm.polygons])
        on_h = lambda p: (lambda r: r[0] is not None and r[3] < 2e-3)(tH.find_nearest(p))
        nm = boolean(h, "DIFFERENCE", cutH); bm = bmesh.new(); bm.from_mesh(nm); bpy.data.meshes.remove(nm); uvl = bm.loops.layers.uv.active
        new = [f for f in bm.faces if not on_h(f.calc_center_median())]
        sx = -1 if hn.endswith("_D") else 1                              # walls of a D-side piece are tested on the mirrored S arm
        def in_arm(f):
            c = h.matrix_world @ f.calc_center_median() - armS.matrix_world.translation; c.x = c.x if c.x < 0 else -c.x
            return inside_arm(c)
        drop = [f for f in new if in_arm(f)] if int(E("HOSTDROP", 0)) else []; keep = [f for f in new if f not in set(drop)]   # default: all kept, the ones doubling an arm wall go in curata_compartimente.py (exact)
        bmesh.ops.delete(bm, geom=drop, context="FACES")
        for f in keep:
            f.material_index = 0; f.smooth = True
            if uvl:
                for lp in f.loops: lp[uvl].uv = (lp.vert.co.x / 256.0, lp.vert.co.y / 256.0)
        n0 = len(hm.polygons); bm.to_mesh(hm); bm.free(); hm.update()
        print("USA COMP %s: suprafata din compartimente scoasa, %d -> %d fete, pereti noi in afara bratului %d (%d in brat sterse)" % (hn, n0, len(hm.polygons), len(keep), len(drop)))
    for hn in [n for n in hosts if n.endswith("_S")]: mirror_into(bpy.data.objects[hn].data, bpy.data.objects[hn[:-2] + "_D"].data); print("USA COMP %s = oglinda lui %s" % (hn[:-2] + "_D", hn))
    for o in list(cutH.objects): bpy.data.objects.remove(o)
    bpy.data.collections.remove(cutH)
    for m0 in BGM: bpy.data.meshes.remove(m0)
    mirror_into(meS, armD.data)
    door = {}
    for gk, dm in doorS.items():
        dD = bpy.data.meshes.new("usa_%s_D" % gk); mirror_into(dm, dD)
        for m_ in dm.materials: dD.materials.append(m_)
        for p in dD.polygons: p.use_smooth = True
        door[gk + "_S"] = (dm, 1); door[gk + "_D"] = (dD, -1)
# --- shape keys: stage 0 closed, 1 raised, 2..NS slid
for sd, (dm, mx) in door.items():
    tmp = bpy.data.objects.new("tmp_" + sd, dm); bpy.context.scene.collection.objects.link(tmp); tmp.shape_key_add(name="inchisa")
    P = np.array([v.co[:] for v in dm.vertices]); FRM = [frame((p[0] * mx, p[1], p[2])) for p in P]
    for k in range(1, NS + 1):
        up = UP * min(1, k / 2); ds = 0 if k <= 2 else int(round(L * (k - 2) / (NS - 2)))
        kb_ = tmp.shape_key_add(name="etapa_%02d" % k, from_mix=False)
        for vi, (i, t, l, n) in enumerate(FRM):
            q = place(i, t, l, n, ds, up); kb_.data[vi].co = (q[0] * mx, q[1], q[2])
    bpy.data.objects.remove(tmp)
def set_stage(o, x):                                                     # x in [0, NS]: blend of two neighbouring stages
    for k in range(1, NS + 1): o.data.shape_keys.key_blocks["etapa_%02d" % k].value = max(0.0, 1 - abs(x - k))
for cn, X in XI.items():
    col = bpy.data.collections[cn]; pre = PRE[cn]
    for n_ in [o.name for o in bpy.data.objects if o.name.startswith((pre + "usa_", pre + "clapa_"))]: bpy.data.objects.remove(bpy.data.objects[n_])
    for sd, (dm, mx) in door.items():
        o = bpy.data.objects.new(pre + "usa_" + sd, dm if cn == "ATELIER_LAME" else dm.copy()); col.objects.link(o); o.location = (X, 0, 0)
        if cn == "ATELIER_DESCHISE": set_stage(o, NS)
        elif cn == "ATELIER_STRANSE": set_stage(o, 0)
        else:
            op = lambda a: [(a + round(FO * j / NS), j) for j in range(NS + 1)]; cl = lambda a: [(a + round(FO * j / NS), NS - j) for j in range(NS + 1)]
            for fr, x in op(1) + cl(FO + FD) + op(FO + 2 * F - FD + 1 - FO) + cl(2 * F + FO):
                set_stage(o, x)
                for kbk in o.data.shape_keys.key_blocks[1:]: kbk.keyframe_insert("value", frame=fr)
# --- check: S and D symmetric, blades never touching the doors or the arms' remaining skin while they come out
from mathutils.bvhtree import BVHTree
sc = bpy.context.scene; col = bpy.data.collections["ATELIER_LAME"]
def bv(o):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); m = oe.to_mesh(); r = BVHTree.FromPolygons([o.matrix_world @ v.co for v in m.vertices], [list(p.vertices) for p in m.polygons]); oe.to_mesh_clear(); return r
blades = [o for o in col.objects if o.name.startswith("at_lama_")]; hosts = [o for o in col.objects if o.name.startswith(("at_usa_", "at_brat_fata_"))]; worst = 0
blades += [o for o in col.objects if o.name.startswith("at_spinare_")]
for fr in range(1, 2 * F + 2 * FO + 1, 2):
    sc.frame_set(fr); bb = [bv(o) for o in blades]; bh = [bv(o) for o in hosts]
    hits = [(blades[i].name[3:], hosts[j].name[3:], len(bb[i].overlap(bh[j]))) for i in range(len(blades)) for j in range(len(hosts)) if bb[i].overlap(bh[j])]
    if hits: worst = max(worst, max(h[2] for h in hits)); print("USA cadru %3d: %s" % (fr, ", ".join("%s x %s (%d)" % h for h in hits[:6])))
print("USA atingeri lame/coloane x usa / brat (toata animatia): %s" % ("niciuna" if worst == 0 else "max %d" % worst))
sc.frame_set(1 + FO)                                                      # doors fully slid: inside the arm (skin below and above)?
for sd in "SD":
    arm = col.objects["at_brat_fata_" + sd]; ta = bv(arm)
    for o in [o for o in col.objects if o.name.startswith("at_usa_") and o.name.endswith(sd)]:
        dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); m = oe.to_mesh(); P = [o.matrix_world @ v.co for v in m.vertices][::40]; oe.to_mesh_clear()
        out = sum(1 for p in P if ta.ray_cast(p, Vector((0, 0, -1)), 300)[0] is None or ta.ray_cast(p, Vector((0, 0, 1)), 300)[0] is None)
        print("USA %s deschisa: %.1f%% din usa iese din brat" % (o.name, 100 * out / len(P)))
sc.frame_set(FO + F); bpy.ops.wm.save_as_mainfile(filepath=OUT)

