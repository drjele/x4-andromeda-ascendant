# Blades on two spiral-staircase spines (asked: no L brackets; round pivots perpendicular to PS, the blades leaving them like a spiral
# staircase - one spine for the front set, one for the back set, on the line of point 7 near the arm's front / back edges; the blades
# keep the front arm's curve since they come down out of it and go back up into it; they come down, then turn into place).
# Per blade: stowed = the front-arm spine curve offset across the arm to its spine (front set at +UF, back set at -UB along the arm's
# across direction) for its length, the lying-V section reaching W m from the spine line towards the arm's middle, open OPEN m, its
# own storey Z (no two storeys overlap), narrowing to the tip; deployed = lowered DROP m along the spine, then turned about the
# spine (vertical) by its angle - chosen per blade so the open blade lies closest to its reference blade (front set opening to +y,
# back set to -y). Spines: round vertical columns (radius RS) from the PS underside down past the lowest blade. Three instances:
# ATELIER_STRANSE (s_), ATELIER_DESCHISE (d_), ATELIER_LAME (at_, animated: 1 stowed, FD lowered, F open, back to 2F).
# Checks: strict hiding of the stowed blades (rays must hit the ship within HD m in all 6 directions) and blade x blade contacts on
# every K-th frame. ZSTEP=d: storeys evenly d m apart in the ZS order (asked: as little height between blades as possible). Spines
# (asked: as short as possible, red, coming out of the arms too): each only spans its blades' roots (+-CM m), material lame_rosu,
# and comes down with them (same drop keys). Asked next: the hinges glued at the top to at_PS_carena / at_PS - the column's top stays
# fixed at max(the PS-carena underside above it + CI m, its blades' top root), only its bottom follows the blades down (scale z keyed,
# origin on the top). Asked next: the back blades did not follow the arm's contour and stowed blades stuck out of the arms - now
# the across offsets are fractions of the arm's own half-width at each point (to the inner contour for the front set, to the outer
# contour for the back set): wide edge at FR * half-width, apex WR * half-width back towards the spine; columns follow.
# Asked next: shorter hinges, blades as close to at_PS_carena / at_PS as possible. DROP=auto: the smallest drop (DMIN.. step DS)
# at which no blade touches the ship, dropped and at every step of its turn; the column's top slides from its stowed top (inside
# PS) down to just inside the carena's underside (+CI), its bottom follows the blades. Old blade / column objects of the same names
# anywhere in the file are removed first (they made the .001 copies).
# Asked next: at_spinare_fata_S too long; every hinge ends with the last blade on it. Each set now has its own drop (DROP=auto
# searched per set, the set's blades only) and ZSET=top: each set's storeys start at the top (ZTOP) going down ZSTEP apart, so the
# front set does not hang under the back one; the column's bottom = the lowest blade's bottom (CMB m margin).
# FO=n: the blades / columns wait n frames stowed at the start and end (for the arm flaps, lame_clapa.py, to open first and close
# last): keys 1, 1+FO stowed, FO+FD dropped, FO+F open, back in reverse to 2F+2FO. Usage: blender -b <in.blend> --python lame_spirala.py -- <out.blend> <linii.npz> ; env (see E(...) below)
import bpy, bmesh, sys, os, json, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT, L = a[0], np.load(a[1]); E = lambda k, d: float(os.environ.get(k, d)); X0 = -1600.0
UF, UB, W, OPEN, SIG, _DROP, RS, HD, F, FD, K = E("UF", 70), E("UB", 70), E("W", 40), E("OPEN", 6), E("SIG", 20), (75.0 if os.environ.get("DROP") == "auto" else E("DROP", 75)), E("RS", 6), E("HD", 120), int(E("F", 60)), int(E("FD", 20)), int(E("K", 4))
ZS = dict((q.split(":")[0], float(q.split(":")[1])) for q in os.environ.get("ZS", "009:21,010:12.6,007:4.2,008:-4.2,014:-12.6,013:-21").split(","))
LEN = dict((q.split(":")[0], float(q.split(":")[1])) for q in os.environ.get("LEN", "007:757,008:542,009:754,010:754,013:754,014:754").split(","))
ZSTEP = E("ZSTEP", 0); CM = E("CM", 3)
if ZSTEP:
    _o = os.environ.get("ZORD", "009,010,014,013,007,008").split(","); ZS = {t: (2.5 - i) * ZSTEP for i, t in enumerate(_o)}
TAG = ["007", "008", "009", "010", "013", "014"]; FRONT = ("007", "008")
XI = {"ATELIER_LAME": -7000.0, "ATELIER_DESCHISE": -9000.0, "ATELIER_STRANSE": -11000.0}; PRE = {"ATELIER_LAME": "at_", "ATELIER_DESCHISE": "d_", "ATELIER_STRANSE": "s_"}
ship = [o for o in bpy.data.collections["ASAMBLAT_NOU"].objects if o.type == "MESH" and not o.name.startswith("an_lama")]
V, Fc = [], []
for o in ship:
    k = len(V); V += [o.matrix_world @ v.co - Vector((X0, 0, 0)) for v in o.data.vertices]; Fc += [[k + i for i in p.vertices] for p in o.data.polygons]
T = BVHTree.FromPolygons(V, Fc); CI = E("CI", 2)
_pc = [o for o in ship if o.name in ("an_PS", "an_PS_carena")]
TP = BVHTree.FromPolygons([o.matrix_world @ v.co - Vector((X0, 0, 0)) for o in _pc for v in o.data.vertices], [[sum(len(q.data.vertices) for q in _pc[:k]) + i for i in p.vertices] for k, o in enumerate(_pc) for p in o.data.polygons])
under = lambda xy: TP.ray_cast(Vector((xy[0], xy[1], -2000)), Vector((0, 0, 1)), 5000)[0].z; dirs = [Vector(d).normalized() for d in ((0, 0, 1), (0, 0, -1), (1, 0, 1), (-1, 0, 1), (0, 1, -1), (0, -1, -1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0))]
hid = lambda p: all(T.ray_cast(Vector(p) + d * .3, d, HD)[0] is not None for d in dirs)
o = bpy.data.objects["g_as_bf_sudat_S"]; LN = json.loads(o["linii"])
def line(nm):
    P = np.array([o.matrix_world @ p.co.xyz for p in o.data.splines[LN.index(nm)].points]) + [3100, 0, 0]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; u = np.arange(0, d[-1], 1.0); return np.c_[[np.interp(u, d, P[:, k]) for k in range(3)]].T
Sp, Ci = line("g_as_bf_spinare_brat_fata_S"), line("g_as_bf_contur_interior_brat_fata_S")
def gsm(A, sig):
    r = int(3 * sig); k = np.exp(-.5 * (np.arange(-r, r + 1) / sig) ** 2); k /= k.sum(); P = np.r_[2 * A[0] - A[r:0:-1], A, 2 * A[-1] - A[-2:-r - 2:-1]]
    return np.c_[[np.convolve(P[:, j], k, mode="valid") for j in range(A.shape[1])]].T
i0 = int(np.argmin(np.linalg.norm(Sp[:, :2] - [-59.6, 74.3], axis=1))); base = gsm(Sp[i0:], SIG)
Tg = np.gradient(base, axis=0); Tg /= np.linalg.norm(Tg, axis=1)[:, None]
from mathutils.kdtree import KDTree
kc = KDTree(len(Ci))
for j, p in enumerate(Ci): kc.insert(p, j)
kc.balance()
Ce = line("g_as_bf_contur_exterior_brat_fata_S"); ke = KDTree(len(Ce))
for j, p in enumerate(Ce): ke.insert(p, j)
ke.balance()
U = np.array([np.array(kc.find(p)[0]) - p for p in base]); U -= Tg * (U * Tg).sum(1)[:, None]; U = gsm(U / np.linalg.norm(U, axis=1)[:, None], SIG); U /= np.linalg.norm(U, axis=1)[:, None]
def hw(kt):
    D = np.array([np.linalg.norm((np.array(kt.find(p)[0]) - p)[:2]) for p in base]); return gsm(D[:, None], SIG)[:, 0]
HWI, HWO = hw(kc), hw(ke); FR, WR = E("FR", .6), E("WR", .35)
N = np.cross(Tg, U); N /= np.linalg.norm(N, axis=1)[:, None]; N[N[:, 2] < 0] *= -1
spine_xy = {"fata": (base[0] + U[0] * FR * HWI[0])[:2], "spate": (base[0] - U[0] * FR * HWO[0])[:2]}
print("SPIRALA semilatimea bratului (spre interior / exterior) la 7: %.0f / %.0f m, la 400 m: %.0f / %.0f m" % (HWI[0], HWO[0], HWI[400], HWO[400]))
def ref_mid(tag):
    nm = "Circle_" + tag; return L[nm + "_mid"]
def blade_stowed(tag):
    n = int(LEN[tag]); n = min(n, len(base) - 1); b = base[:n + 1]; u = U[:n + 1]; nn = N[:n + 1]; t = np.arange(n + 1, dtype=float); TAP = min(250.0, n * .35)
    tp = np.clip(1 - np.logaddexp(0, (t - (n - TAP)) / 20) * 20 / TAP, 0, 1)
    side = 1 if tag in FRONT else -1; H = (HWI if tag in FRONT else HWO)[:n + 1]
    wide = b + u * side * (FR * H)[:, None] + nn * ZS[tag]; apex = wide - u * side * (WR * H * tp)[:, None]
    Ms, Mj = wide + nn * (OPEN / 2 * tp)[:, None], wide - nn * (OPEN / 2 * tp)[:, None]
    return np.stack([Ms, Mj, apex], 1)
f_ = np.linspace(0, 1, 7)[:-1]
def ring(RW): Ms, Mj, Va = RW[:, 0], RW[:, 1], RW[:, 2]; return np.stack([Ms + (Va - Ms) * t for t in f_] + [Va + (Mj - Va) * t for t in f_] + [Mj + (Ms - Mj) * t for t in f_], axis=1)
def build(name, R, mirror):
    bm = bmesh.new(); P = R * ([-1, 1, 1] if mirror else 1); n, m = P.shape[:2]
    vv = [[bm.verts.new(tuple(P[i, j])) for j in range(m)] for i in range(n)]
    for i in range(n - 1):
        for j in range(m):
            q = [vv[i][j], vv[i][(j + 1) % m], vv[i + 1][(j + 1) % m], vv[i + 1][j]]; bm.faces.new(q[::-1] if mirror else q)
    for row, rev in ((vv[0], not mirror), (vv[-1], mirror)):
        f = bm.faces.new(row[::-1] if rev else row); bmesh.ops.triangulate(bm, faces=[f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    at = me.attributes.new("sharp_edge", "BOOLEAN", "EDGE"); Kk = m // 3
    for e in me.edges:
        i0_, i1_ = sorted(e.vertices); at.data[e.index].value = (i1_ - i0_ == m and i0_ % m in (0, Kk, 2 * Kk))
    for p in me.polygons: p.use_smooth = True
    mt = bpy.data.materials.get("lame_rosu")
    if mt: me.materials.append(mt)
    return me
def rotz(P, c, th):
    cs, sn = math.cos(th), math.sin(th); Q = P.copy(); x, y = P[..., 0] - c[0], P[..., 1] - c[1]; Q[..., 0] = c[0] + cs * x - sn * y; Q[..., 1] = c[1] + sn * x + cs * y; return Q
def blade_bvh(P): return BVHTree.FromPolygons([Vector(p) for p in P.reshape(-1, 3)], [[i * 18 + j, i * 18 + (j + 1) % 18, (i + 1) * 18 + (j + 1) % 18, (i + 1) * 18 + j] for i in range(len(P) - 1) for j in range(18)])
def fit(tag, drop):
    RW = blade_stowed(tag); c = spine_xy["fata" if tag in FRONT else "spate"]; low = RW - [0, 0, drop]; rm = ref_mid(tag); best = None
    for thd in np.arange(0, 91, 1.0):
        th = math.radians(-thd if tag in FRONT else thd); mid = rotz(low, c, th).mean(1); d = np.mean([np.min(np.linalg.norm(rm - p, axis=1)) for p in mid[::15]])
        if best is None or d < best[0]: best = (d, th)
    return RW, c, low, best
if os.environ.get("ZSET") == "top":
    for _set in (["009", "010", "014", "013"], ["007", "008"]):
        for i, t in enumerate(_set): ZS[t] = E("ZTOP", 9.75) - i * ZSTEP
DROPS = {"fata": _DROP, "spate": _DROP}
for _st, _tags in (("fata", [t for t in TAG if t in FRONT]), ("spate", [t for t in TAG if t not in FRONT])):
  if os.environ.get("DROP") != "auto": break
  for DROP in np.arange(E("DMIN", 20), 151, E("DS", 5)):
        ok = True
        for tag in _tags:
            RW, c, low, best = fit(tag, DROP)
            for th in np.linspace(0, best[1], 7):
                if T.overlap(blade_bvh(ring(rotz(low, c, th)))): ok = False; break
            if not ok: break
        if ok: DROPS[_st] = DROP; print("SPIRALA set %s: coborare minima %.0f m" % (_st, DROP)); break
FO = int(E("FO", 0))
KF = lambda a_, b_, c_: [(1, a_)] + ([(1 + FO, a_)] if FO else []) + [(FO + FD, b_), (FO + F, c_), (FO + 2 * F - FD + 1, b_), (FO + 2 * F, a_)] + ([(2 * FO + 2 * F, a_)] if FO else [])
plan = {}
for tag in TAG:
    st = "fata" if tag in FRONT else "spate"; DROP = DROPS[st]; RW, c, low, best = fit(tag, DROP)
    plan[tag] = (RW, c, best[1], best[0])
    _pts = ring(RW).reshape(-1, 3)[::5]; ex = np.mean([not hid(p) for p in _pts]); exv = np.mean([not all(T.ray_cast(Vector(p) + d * .3, d, HD)[0] is not None for d in dirs[:2]) for p in _pts])
    print("SPIRALA %s (set %s): %d m, etaj %+.1f m, spinarea la %s; stransa expusa (strict) %.1f%%, de sus/jos %.1f%%; deschisa: coborata %.0f m + rotita %+.0f grade, fata de lama din referinta %.0f m (medie)" % (tag, st, len(RW), ZS[tag], np.round(c, 1), 100 * ex, 100 * exv, DROP, math.degrees(best[1]), best[0]))
for cn, X in XI.items():
    col = bpy.data.collections[cn]; pre = PRE[cn]
    for n_ in [x.name for x in bpy.data.objects if x.name.startswith((pre + "lama_", pre + "spinare_"))]: bpy.data.objects.remove(bpy.data.objects[n_])
    for m_ in [x for x in bpy.data.meshes if x.users == 0 and x.name.startswith((pre + "lama_", pre + "spinare_"))]: bpy.data.meshes.remove(m_)
    for st, c in spine_xy.items():
        zz = np.concatenate([np.r_[ring(RW)[:3].reshape(-1, 3)[:, 2]] for t_, (RW, c_, th_, d_) in plan.items() if (t_ in FRONT) == (st == "fata")])
        zlo, zhi = zz.min() - E("CMB", .5), zz.max() + CM; DROP = DROPS[st]; ztop = max(under(c) + CI, zhi)
        for sd, sg in (("S", 1), ("D", -1)):
            bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=RS, radius2=RS, depth=1.0); bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, -.5))
            me = bpy.data.meshes.new(pre + "spinare_%s_%s" % (st, sd)); bm.to_mesh(me); bm.free()
            for p in me.polygons: p.use_smooth = True
            mt = bpy.data.materials.get("lame_rosu")
            if mt: me.materials.append(mt)
            so = bpy.data.objects.new(pre + "spinare_%s_%s" % (st, sd), me); me.name = so.name; col.objects.link(so); xy = (X + sg * c[0], c[1]); zd = min(zhi, under(c) + CI)
            st_ = (Vector((*xy, zhi)), zhi - zlo); dn_ = (Vector((*xy, zd)), zd - zlo + DROP)
            if cn == "ATELIER_STRANSE": so.location, so.scale.z = st_
            elif cn == "ATELIER_DESCHISE": so.location, so.scale.z = dn_
            else:
                for fr, (lo, h) in KF(st_, dn_, dn_):
                    so.location, so.scale.z = lo, h; so.keyframe_insert("location", frame=fr); so.keyframe_insert("scale", index=2, frame=fr)
        if cn == "ATELIER_LAME": print("SPIRALA coloana %s: strans %.1f m (in PS); deschis lipita sus la z %.1f (dedesubtul PS / carena %.1f), %.1f m lunga" % (st, zhi - zlo, zd, under(c), zd - zlo + DROP))
    for tag, (RW, c, th, d) in plan.items():
        R = ring(RW)
        for sd, mir in (("S", False), ("D", True)):
            DROP = DROPS["fata" if tag in FRONT else "spate"]; cc = Vector((-c[0] if mir else c[0], c[1], 0)); me = build(pre + "lama_%s_%s" % (tag, sd), R, mir); me.transform(Matrix.Translation(-cc))
            ob = bpy.data.objects.new(pre + "lama_%s_%s" % (tag, sd), me); me.name = ob.name; col.objects.link(ob); ob.rotation_mode = "XYZ"; thz = -th if mir else th
            stow, low, open_ = (cc + Vector((X, 0, 0)), 0.0), (cc + Vector((X, 0, -DROP)), 0.0), (cc + Vector((X, 0, -DROP)), thz)
            if cn == "ATELIER_STRANSE": ob.location, ob.rotation_euler.z = stow[0], stow[1]
            elif cn == "ATELIER_DESCHISE": ob.location, ob.rotation_euler.z = open_[0], open_[1]
            else:
                for fr, (loc, rz) in KF(stow, low, open_):
                    ob.location, ob.rotation_euler.z = loc, rz; ob.keyframe_insert("location", frame=fr); ob.keyframe_insert("rotation_euler", index=2, frame=fr)
sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, 2 * F + 2 * FO
blades = [x for x in bpy.data.collections["ATELIER_LAME"].objects if x.name.startswith("at_lama_")]; worst = 0
for fr in list(range(1, FO + F + 1, K)) + [FO + F]:
    sc.frame_set(fr); bv = [BVHTree.FromPolygons([x.matrix_world @ v.co for v in x.data.vertices], [list(p.vertices) for p in x.data.polygons]) for x in blades]
    hits = [(blades[i].name, blades[j].name, len(bv[i].overlap(bv[j]))) for i in range(len(blades)) for j in range(i + 1, len(blades)) if bv[i].overlap(bv[j])]
    if hits: worst = max(worst, max(h[2] for h in hits)); print("SPIRALA cadru %3d: %s" % (fr, ", ".join("%s x %s (%d)" % (h[0][8:], h[1][8:], h[2]) for h in hits[:6])))
print("SPIRALA contacte intre lame pe toata animatia: %s" % ("niciunul" if worst == 0 else "max %d" % worst))
sc.frame_set(FO + F); bpy.ops.wm.save_as_mainfile(filepath=OUT)
