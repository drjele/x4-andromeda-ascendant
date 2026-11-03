# Puts the front arm rebuilt on the cleaned guides into the scene (asked: guides separately with clean lines, surfaces redone,
# reassembled): (1) an_/at_brat_fata_S get the new vertex positions (brat_pe_ghidaje_curate.py), _D = their exact mirror (same vertex
# order, checked); (2) the red nacelle (an_/at_nacela_inchis / _deschis) follows its three contours old -> clean (each vertex moved by
# the inverse-distance blend of the three contours' moves), so its rims stay on the arm's mouth; (3) the decorations sitting on the
# arm (lacrima_brat, decor_R060) move with the arm's skin under them (8 nearest arm vertices); (4) the assembled guides
# g_as_bf_sudat_S/D and g_as_nac_sudat_S/D redrawn from the clean lines (names / order kept) and the clean lines drawn separately in
# GHIDAJ_BRAT_CURAT at x XS (arm red, nacelle blue). Usage: blender -b <scene> --python aplica_brat_curat.py -- <old guides npz>
# <clean guides npz> <new arm npz> <out.blend>   env XS=-13000 GX=3100
import bpy, sys, os, json, numpy as np
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index("--") + 1:]; G0, G1 = np.load(a[0], allow_pickle=True), np.load(a[1], allow_pickle=True); NEW = np.load(a[2], allow_pickle=True)["at_brat_fata_S__v"]; OUT = a[3]
XS, GX = float(os.environ.get("XS", -13000)), float(os.environ.get("GX", 3100)); MX = np.array([-1, 1, 1])
def getv(me): A = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", A); return A.reshape(-1, 3)
def setv(me, P): me.vertices.foreach_set("co", P.astype(np.float32).ravel()); me.update()
def kd(P):
    t = KDTree(len(P))
    for i, p in enumerate(P): t.insert(p, i)
    t.balance(); return t
def mirror_ok(S, D):
    t = kd(S * MX); return max(t.find(p)[2] for p in D[:: max(1, len(D) // 3000)]), all(np.allclose(S[i] * MX, D[i], atol=1e-3) for i in range(0, len(S), max(1, len(S) // 500)))
def setSD(base, PS):
    for pre in ("an_", "at_"):
        S, D = bpy.data.objects[pre + base + "_S"].data, bpy.data.objects[pre + base + "_D"].data; same = mirror_ok(getv(S), getv(D))[1]
        setv(S, PS)
        if same: setv(D, PS * MX)
        else: print("APLIC ATENTIE %s%s_D nu are aceeasi ordine a varfurilor - nemodificat" % (pre, base))
    print("APLIC %s: S nou, D oglinda" % base)
# (1) arm
V0 = getv(bpy.data.objects["at_brat_fata_S"].data); setSD("brat_fata", NEW); mvA = np.linalg.norm(NEW - V0, axis=1)
# (2) nacelle: contour moves (old and clean resampled at the same fractions)
def frac(P, n):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; u = np.linspace(0, d[-1], n); return np.c_[[np.interp(u, d, P[:, k]) for k in range(3)]].T
CT = []
for k in ("g_as_nac_contur_nacela_capat1_S", "g_as_nac_contur_nacela_capat2_S", "g_as_nac_contur_nacela_varf_S"):
    n = 4000; O_, N_ = frac(G0[k], n), frac(G1[k], n); CT.append((kd(O_), N_ - O_))
for base in ("nacela_inchis", "nacela_deschis"):
    P = getv(bpy.data.objects["at_%s_S" % base].data); Q = P.copy()
    for i, p in enumerate(P):
        ws, ds = [], []
        for t, DD in CT:
            co, j, d = t.find(p); ws.append(1 / (d * d + .01)); ds.append(DD[j])
        ws = np.array(ws); Q[i] = p + (ws[:, None] * np.array(ds)).sum(0) / ws.sum()
    setSD(base, Q); print("APLIC %s: mutat max %.2f m" % (base, np.linalg.norm(Q - P, axis=1).max()))
# (3) decorations on the arm
tA = kd(V0); DA = NEW - V0
for base in ("lacrima_brat", "decor_R060"):
    P = getv(bpy.data.objects["at_%s_S" % base].data); Q = P.copy()
    for i, p in enumerate(P):
        nb = tA.find_n(p, 8); w = np.array([1 / (d * d + .01) for _, _, d in nb]); Q[i] = p + (w[:, None] * DA[[j for _, j, _ in nb]]).sum(0) / w.sum()
    setSD(base, Q); print("APLIC %s: mutat max %.2f m" % (base, np.linalg.norm(Q - P, axis=1).max()))
# (4) guides
def redraw(obj, LN, side):
    cu = obj.data; cu.splines.clear()
    for nm in LN:
        P = G1[nm.replace("_D", "_S") if side == "D" else nm] * (MX if side == "D" else 1) - [GX if side == "S" else -GX, 0, 0]
        sp = cu.splines.new("POLY"); sp.points.add(len(P) - 1)
        for p, q in zip(sp.points, P): p.co = (q[0], q[1], q[2], 1)
for gn in ("g_as_bf_sudat", "g_as_nac_sudat"):
    for side in "SD":
        o = bpy.data.objects[gn + "_" + side]; LN = json.loads(o["linii"]); redraw(o, LN, side)
    print("APLIC ghidaje %s_S/D redesenate din liniile curate" % gn)
col = bpy.data.collections.get("GHIDAJ_BRAT_CURAT") or bpy.data.collections.new("GHIDAJ_BRAT_CURAT")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
for nm, rgb in [(k, (.9, .1, .1, 1)) for k in G1.files if k.startswith("g_as_bf_")] + [(k, (.1, .4, 1, 1)) for k in G1.files if k.startswith("g_as_nac_contur")]:
    cu = bpy.data.curves.new("gc_" + nm[5:], "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.2; sp = cu.splines.new("POLY"); P = G1[nm]; sp.points.add(len(P) - 1)
    for p, q in zip(sp.points, P): p.co = (q[0] + XS, q[1], q[2], 1)
    m = bpy.data.materials.get("gc_" + str(rgb)) or bpy.data.materials.new("gc_" + str(rgb)); m.diffuse_color = rgb; cu.materials.append(m)
    o = bpy.data.objects.new("gc_" + nm[5:], cu); o.color = rgb; col.objects.link(o)
print("APLIC GHIDAJ_BRAT_CURAT: %d linii la x %.0f; brat mutat medie %.2f max %.2f m" % (len(col.objects), XS, mvA.mean(), mvA.max()))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
