# The front arm opens before the blades come out and closes after (asked: one side flap - the arm's underside, hinged on one edge,
# swings down): in each workshop instance the arm's (at_/d_/s_brat_fata_S, D mirrored) downward faces lying under the blades - from
# point 7 along the arm spine for S1 m, across from -(FR+MG) x outer half-width to +(FR+MG) x inner half-width - are cut out of the
# arm (the three instances share one arm mesh, separate from the ship's) into flap segments <pre>clapa_<k>_S/D, NSEG along the arm
# (the arm curves, so each segment turns about its own straight hinge = a chord of ONE smoothed hinge curve along the flap's edge on
# the HINGE side, ext / int, so neighbours turn alike).
# Each segment: thickness TH m (solidify, applied), ANG degrees open. Timing in ATELIER_LAME: flap 1 -> 1+FO opens, stays open,
# 2F+FO -> 2F+2FO closes (the blades wait FO frames: lame_spirala.py FO=). Checks flaps x blades on every K-th frame.
# Usage: blender -b <in.blend> --python lame_clapa.py -- <out.blend> ; env FR=.6 MG=.2 S1=770 NSEG=32 HINGE=ext ANG=180 TH=1.5 FO=15 F=60 K=3
import bpy, bmesh, sys, os, json, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
OUT = sys.argv[sys.argv.index("--") + 1]; E = lambda k, d: float(os.environ.get(k, d))
FR, MG, S1, NSEG, ANG, TH, FO, F, K, SIG = E("FR", .6), E("MG", .2), E("S1", 770), int(E("NSEG", 32)), E("ANG", 180), E("TH", 1.5), int(E("FO", 15)), int(E("F", 60)), int(E("K", 3)), E("SIG", 20)
HINGE = os.environ.get("HINGE", "ext")   # ext + ANG 180 = folded flat outwards, clear of both sets (int or <180 hits the blades)
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
i0 = int(np.argmin(np.linalg.norm(Sp[:, :2] - [-59.6, 74.3], axis=1))); base = gsm(Sp[i0:], SIG)
Tg = np.gradient(base, axis=0); Tg /= np.linalg.norm(Tg, axis=1)[:, None]; kc, ke = kd(Ci), kd(Ce)
U = np.array([np.array(kc.find(p)[0]) - p for p in base]); U -= Tg * (U * Tg).sum(1)[:, None]; U = gsm(U / np.linalg.norm(U, axis=1)[:, None], SIG); U /= np.linalg.norm(U, axis=1)[:, None]
hw = lambda t: gsm(np.array([np.linalg.norm((np.array(t.find(p)[0]) - p)[:2]) for p in base])[:, None], SIG)[:, 0]
HWI, HWO = hw(kc), hw(ke); kb = kd(np.c_[base[:, :2], np.zeros(len(base))])
def arm_coords(p):                                                       # ship-coords point -> (s along the spine, across l)
    _, i, _ = kb.find((p[0], p[1], 0)); return i, float((np.array(p) - base[i])[:2] @ U[i][:2])
# --- cut once (S half of the shared mesh), build flap pieces in ship coords
arm = bpy.data.objects["at_brat_fata_S"]; me = arm.data; bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
sel = []
for f in bm.faces:
    if abs(f.normal.z) < .2: continue                                   # the arm's normals point inwards: underside = flat-ish faces below the spine
    c = f.calc_center_median(); i, l = arm_coords(c)
    if i >= S1 or c.z > base[i][2]: continue
    if -(FR + MG) * HWO[i] <= l <= (FR + MG) * HWI[i]: sel.append(f)
print("CLAPA: %d fete din dedesubtul bratului taiate" % len(sel))
segs = [[] for _ in range(NSEG)]
for f in sel:
    i, _ = arm_coords(f.calc_center_median()); segs[min(NSEG - 1, int(i / S1 * NSEG))].append([tuple(v.co) for v in f.verts])
bmesh.ops.delete(bm, geom=sel, context="FACES"); bm.to_mesh(me); bm.free(); me.update()
side = -1 if HINGE == "ext" else 1
allV = np.array([v for seg in segs for f in seg for v in f]); inf = [arm_coords(p) for p in allV[::3]]; aV = allV[::3]
aS = np.array([a for a, b in inf]); aL = np.array([b for a, b in inf]); hp = []
for i in range(0, int(S1)):                                              # one smooth hinge curve = the flap's hinge-side edge, smoothed
    m = np.abs(aS - i) <= 3
    hp.append(aV[m][np.argmax(side * aL[m])] if m.any() else (hp[-1] if hp else base[0]))
HP = gsm(np.array(hp), 15)
pieces = []
for k, faces in enumerate(segs):
    if not faces: continue
    vid = {}; V = []; Fs = []
    for f in faces:
        q = []
        for v in f:
            key = tuple(round(x, 4) for x in v)
            if key not in vid: vid[key] = len(V); V.append(v)
            q.append(vid[key])
        Fs.append(q)
    V = np.array(V); info = [arm_coords(p) for p in V]; sI = np.array([a for a, b in info]); lI = np.array([b for a, b in info])
    pa, pb = HP[int(min(sI.min(), S1 - 1))], HP[int(min(sI.max(), S1 - 1))]
    ax = (pb - pa) / np.linalg.norm(pb - pa); cen = V.mean(0)
    test = Matrix.Rotation(math.radians(30), 3, Vector(ax)) @ Vector(cen - pa)
    sgn = 1 if test.z < (cen - pa)[2] else -1                            # the way that swings the flap down
    pieces.append((k, V - pa, Fs, pa, ax, sgn))
print("CLAPA: %d segmente, balama pe marginea %s" % (len(pieces), "dinafara (exterior)" if HINGE == "ext" else "dinauntru (interior)"))
mat = arm.data.materials[0] if arm.data.materials else None
for cn, X in XI.items():
    col = bpy.data.collections[cn]; pre = PRE[cn]
    for n_ in [o.name for o in bpy.data.objects if o.name.startswith(pre + "clapa_")]: bpy.data.objects.remove(bpy.data.objects[n_])
    for k, Vl, Fs, pa, ax, sgn in pieces:
        for sd, mir in (("S", False), ("D", True)):
            nm = pre + "clapa_%02d_%s" % (k, sd); m = bpy.data.meshes.new(nm); Vm = Vl * ([-1, 1, 1] if mir else 1)
            m.from_pydata([tuple(v) for v in Vm], [], [q[::-1] for q in Fs] if mir else Fs); bm2 = bmesh.new(); bm2.from_mesh(m)
            bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces)
            r = bmesh.ops.extrude_face_region(bm2, geom=bm2.faces[:]); vv = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
            for v in vv: v.co.z += TH
            bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces); bm2.to_mesh(m); bm2.free()
            for p in m.polygons: p.use_smooth = True
            if mat: m.materials.append(mat)
            o = bpy.data.objects.new(nm, m); col.objects.link(o); P0 = Vector(pa * ([-1, 1, 1] if mir else 1)); o.location = P0 + Vector((X, 0, 0))
            o.rotation_mode = "AXIS_ANGLE"; axm = Vector(ax * ([-1, 1, 1] if mir else 1)); a_open = math.radians(ANG) * sgn * (-1 if mir else 1)
            o.rotation_axis_angle = (0, *axm)
            if cn == "ATELIER_DESCHISE": o.rotation_axis_angle = (a_open, *axm)
            elif cn == "ATELIER_LAME":
                for fr, a in ((1, 0), (1 + FO, a_open), (2 * F + FO, a_open), (2 * F + 2 * FO, 0)):
                    o.rotation_axis_angle = (a, *axm); o.keyframe_insert("rotation_axis_angle", frame=fr)
sc = bpy.context.scene; col = bpy.data.collections["ATELIER_LAME"]
fl = [o for o in col.objects if o.name.startswith("at_clapa_")]; bl = [o for o in col.objects if o.name.startswith(("at_lama_", "at_spinare_"))]; worst = 0
bvh = lambda o: BVHTree.FromPolygons([o.matrix_world @ v.co for v in o.data.vertices], [list(p.vertices) for p in o.data.polygons])
for fr in list(range(1, FO + F + 1, K)):
    sc.frame_set(fr); bf = [bvh(o) for o in fl]; bb = [bvh(o) for o in bl]
    hits = [(fl[i].name[3:], bl[j].name[3:], len(bf[i].overlap(bb[j]))) for i in range(len(fl)) for j in range(len(bl)) if bf[i].overlap(bb[j])]
    if hits: worst = max(worst, max(h[2] for h in hits)); print("CLAPA cadru %3d: %s" % (fr, ", ".join("%s x %s (%d)" % h for h in hits[:5])))
print("CLAPA atingeri clapa x lame / balamale: %s" % ("niciuna" if worst == 0 else "max %d" % worst))
sc.frame_set(FO + F); bpy.ops.wm.save_as_mainfile(filepath=OUT)
