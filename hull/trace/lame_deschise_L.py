# Deployed blades in our style, tied to PS by L brackets, none crossing (asked: the d_PS blades in our style, joined to d_PS by Ls
# without intercrossing; Ls: short leg down out of the PS bottom, long leg across to the blade; their mounts in a row along the PS
# bottom edge). In ATELIER_DESCHISE (x XB): each blade (piese/ghid_lama_<nr>_v5.npz, deployed rows) trimmed from the root, KS rows at a
# time, until it touches no other blade (S and D); rebuilt closed (lying V, sharp long edges, lame_rosu) as d_lama_<nr>_S/D. Each L:
# mount = the point of the PS frame's bottom outline (z of its underside) nearest to the blade's root, kept SP m from the mounts already
# used; path mount -> straight down to the root's height -> straight across to the root (wide side middle), corner rounded RC; a square
# bar BW m. Checks: blades x blades, Ls x blades (other than its own), Ls x Ls. D = mirror.
# XMIN: every root kept at least XMIN m off the axis (so the S and D Ls do not meet in the middle). DZ=t:dz,... raises / lowers whole blades (a fan in storeys) so less has to be cut at the roots; each L takes the first mount (nearest
# first) whose bar touches no other blade and no L already placed.
# Usage: blender -b <in.blend> --python lame_deschise_L.py -- <out.blend> <piese dir> <ver> <tags> ; env XB=-9000 KS=4 SP=20 BW=6 RC=8 DZ=
import bpy, bmesh, sys, os, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT, PD, VER, TAGS = a[0], a[1], a[2], a[3].split(","); E = lambda k, d: float(os.environ.get(k, d))
XB, KS, SP, BW, RC = E("XB", -9000), int(E("KS", 4)), E("SP", 20), E("BW", 6), E("RC", 8)
col = bpy.data.collections["ATELIER_DESCHISE"]; mat = bpy.data.materials.get("lame_rosu")
for n in [o.name for o in col.objects if o.name.startswith(("d_lama_", "d_L_"))]: bpy.data.objects.remove(bpy.data.objects[n])
f_ = np.linspace(0, 1, 7)[:-1]
def ring(Ms, Mj, Va): return np.stack([Ms + (Va - Ms) * t for t in f_] + [Va + (Mj - Va) * t for t in f_] + [Mj + (Ms - Mj) * t for t in f_], axis=1)
def bvh_rows(R):
    n, m = R.shape[:2]; verts = [Vector(p) for p in R.reshape(-1, 3)]; faces = [[i * m + j, i * m + (j + 1) % m, (i + 1) * m + (j + 1) % m, (i + 1) * m + j] for i in range(n - 1) for j in range(m)]
    faces += [list(range(m)), [ (n - 1) * m + j for j in range(m)]]; return BVHTree.FromPolygons(verts, faces)
B = {}
for t in TAGS:
    G = np.load(os.path.join(PD, "ghid_lama_%s_%s.npz" % (t, VER))); R = ring(G["lama_margine_sus"], G["lama_margine_jos"], G["lama_varf"])
    B[t] = R
DZ = dict((q.split(":")[0], float(q.split(":")[1])) for q in os.environ.get("DZ", "").split(",") if q)
for t in B: B[t] = B[t] + [0, 0, DZ.get(t, 0.0)]
cut = {t: 0 for t in TAGS}
for it in range(60):                                                      # trim roots until nobody touches anybody
    changed = False; mats = {(t, sd): (B[t][cut[t]:] * ([-1, 1, 1] if sd == "D" else 1)) for t in TAGS for sd in "SD"}; bv = {k: bvh_rows(v) for k, v in mats.items()}
    for t in TAGS:
        others = [k for k in bv if k != (t, "S")]
        rx = ((B[t][cut[t], 0] + B[t][cut[t], 12]) / 2)[0]
        if any(bv[(t, "S")].overlap(bv[k]) for k in others) or rx > -E("XMIN", 25):
            cut[t] += KS; changed = True
    if not changed: break
print("TAIERE la radacina (randuri de 1 m): " + ", ".join("%s %d m" % (t, cut[t]) for t in TAGS))
def build(name, R, mirror):
    bm = bmesh.new(); P = R * ([-1, 1, 1] if mirror else 1); n, m = P.shape[:2]
    vv = [[bm.verts.new(tuple(P[i, j])) for j in range(m)] for i in range(n)]
    for i in range(n - 1):
        for j in range(m):
            q = [vv[i][j], vv[i][(j + 1) % m], vv[i + 1][(j + 1) % m], vv[i + 1][j]]; bm.faces.new(q[::-1] if mirror else q)
    for row, rev in ((vv[0], not mirror), (vv[-1], mirror)):
        f = bm.faces.new(row[::-1] if rev else row); bmesh.ops.triangulate(bm, faces=[f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    at = me.attributes.new("sharp_edge", "BOOLEAN", "EDGE"); K = m // 3
    for e in me.edges:
        i0, i1 = sorted(e.vertices); at.data[e.index].value = (i1 - i0 == m and i0 % m in (0, K, 2 * K))
    for p in me.polygons: p.use_smooth = True
    if mat: me.materials.append(mat)
    return me
rama = bpy.data.objects["d_PS_rama"]; RV = np.array([rama.matrix_world @ v.co for v in rama.data.vertices]) - [XB, 0, 0]
zb = RV[:, 2].min(); edge = RV[(RV[:, 2] < zb + .5) & (RV[:, 0] < 0)]; cen = edge[:, :2].mean(0)
dist_c = np.linalg.norm(edge[:, :2] - cen, axis=1); outline = edge[dist_c > np.percentile(dist_c, 60)]; outline = outline[outline[:, 0] < -E("XMOUNT", 30)]   # the outer bottom rim (S side), mounts off the axis
def sweep(path, w):                                                       # square bar along a polyline
    T = np.gradient(path, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]; up = np.array([0, 0, 1.])
    verts, faces = [], []; n = len(path)
    for i, p in enumerate(path):
        u = up - T[i] * (T[i] @ up)
        if np.linalg.norm(u) < 1e-3: u = np.array([1., 0, 0]) - T[i] * T[i][0]
        u /= np.linalg.norm(u); v = np.cross(T[i], u)
        for du, dv in ((1, 1), (-1, 1), (-1, -1), (1, -1)): verts.append(p + (u * du + v * dv) * w / 2)
    for i in range(n - 1):
        for j in range(4): faces.append([i * 4 + j, i * 4 + (j + 1) % 4, (i + 1) * 4 + (j + 1) % 4, (i + 1) * 4 + j])
    faces += [[3, 2, 1, 0], [(n - 1) * 4 + j for j in range(4)]]; return verts, faces
used = []; Lp = {}; placed = {}
for t in TAGS: placed[("lama", t)] = bvh_rows(B[t][cut[t]:]); placed[("lamaD", t)] = bvh_rows(B[t][cut[t]:] * [-1, 1, 1])
def lpath(mnt, root):
    zc = min(root[2], mnt[2] - 10); c1 = np.array([mnt[0], mnt[1], zc]); r = min(RC, abs(mnt[2] - zc) / 2, np.linalg.norm(root[:2] - mnt[:2]) / 2)
    d2 = root - c1; d2 /= np.linalg.norm(d2); seg1 = np.linspace(mnt + [0, 0, 2], c1 + [0, 0, r], 6)
    th = np.linspace(0, 1, 8)[1:-1]; corner = [(1 - s_) ** 2 * (c1 + [0, 0, r]) + 2 * (1 - s_) * s_ * c1 + s_ ** 2 * (c1 + d2 * r) for s_ in th]
    return np.r_[seg1, corner, np.linspace(c1 + d2 * r, root, 8)], zc, c1
for t in TAGS:
    R = B[t][cut[t]:]; root = (R[0, 0] + R[0, 12]) / 2
    cand = sorted(outline, key=lambda q: np.linalg.norm(q[:2] - root[:2])); pick = None
    for q in cand[::3]:
        if any(np.linalg.norm(q[:2] - u_[:2]) < SP for u_ in used): continue
        path, zc, c1 = lpath(q, root); vs, fs = sweep(path, BW); bl = BVHTree.FromPolygons([Vector(v) for v in vs], fs)
        hit = [k for k, b_ in placed.items() if k != ("lama", t) and bl.overlap(b_)]
        if not hit: pick = (q, path, zc, c1); break
    if pick is None: q = cand[0]; path, zc, c1 = lpath(q, root); pick = (q, path, zc, c1); print("L %s: niciun punct fara atingere, ales cel mai apropiat" % t)
    mnt, path, zc, c1 = pick; used.append(mnt); Lp[t] = path; vs, fs = sweep(path, BW)
    placed[("L", t)] = BVHTree.FromPolygons([Vector(v) for v in vs], fs); placed[("LD", t)] = BVHTree.FromPolygons([Vector(v) * Vector((-1, 1, 1)) for v in vs], fs)
    for sd, mir in (("S", False), ("D", True)):
        me = build("d_lama_%s_%s" % (t, sd), R, mir); o = bpy.data.objects.new(me.name, me); col.objects.link(o); o.location = (XB, 0, 0)
        P = path * ([-1, 1, 1] if mir else 1); vs2, fs2 = sweep(P, BW); m2 = bpy.data.meshes.new("d_L_%s_%s" % (t, sd)); m2.from_pydata([tuple(v) for v in vs2], [], fs2)
        if mir: m2.flip_normals()
        m2.materials.append(bpy.data.materials.get("Material_8") or mat)
        o2 = bpy.data.objects.new(m2.name, m2); col.objects.link(o2); o2.location = (XB, 0, 0)
    print("L %s: prins pe marginea PS la %s, colt la z %.1f, pana la radacina %s (brat scurt %.0f m, brat lung %.0f m)" % (t, np.round(mnt, 1), zc, np.round(root, 1), mnt[2] - zc, np.linalg.norm(root - c1)))
objs = [o for o in col.objects if o.name.startswith(("d_lama_", "d_L_"))]; bv = {o.name: BVHTree.FromPolygons([o.matrix_world @ v.co for v in o.data.vertices], [list(p.vertices) for p in o.data.polygons]) for o in objs}
bad = []
for i, x in enumerate(objs):
    for y in objs[i + 1:]:
        tx, ty = x.name.split("_")[2], y.name.split("_")[2]; sx, sy = x.name[-1], y.name[-1]
        if tx == ty and sx == sy: continue                                # an L touches its own blade - that is the joint
        ov = bv[x.name].overlap(bv[y.name])
        if ov: bad.append("%s x %s (%d)" % (x.name[2:], y.name[2:], len(ov)))
print("VERIF: %s" % ("nicio intersectie intre lame / L-uri (in afara L-ului cu lama lui)" if not bad else "; ".join(bad[:12])))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
