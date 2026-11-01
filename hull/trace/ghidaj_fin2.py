# R109 shark-fin guides, round 2 (variant A confirmed; asked: the base an isosceles V triangle, the 45 deg back edge doubled so the
# thickness carries on into the back, the same curvature on the spine for every rib, clean lines). Local frame: length along +y
# (front = +y), width x, up z, base = the plane z = 0, apex above y = 0, base from y = YB = H/tan(ANG) to the front tip y = L.
#   g_fin_A_profil          spine (x = 0): centre of the back face (45 deg) -> apex rounded by a circle of radius RA tangent to both edges ->
#                           leading edge H*(1 - t^PL) down to the front tip
#   g_fin_A_profil_spate_S/D the back face's side edges: from the base's back corners (+-W/2, YB, 0) along the 45 deg back edge
#                           to the apex, x tapering to 0 there: the back face is a triangle closing at the apex
#   g_fin_A_baza            the base: isosceles triangle, back side y = YB, sides to the front tip blunted by a circle of radius RT
#                           tangent to them, its nose at y = L
#   g_fin_A_sectiune_*      ribs: the spine circle of radius RS (same on every rib) centred RS under the spine, straight lines
#                           tangent to it down to the base corners (+-w, 0) in front, or to the back face's edges (+-we, ze) in the
#                           back (closed across the back face); a rib too low for RS = the arc through its corners and its top
# Usage: blender -b <scene.blend> --python ghidaj_fin2.py -- <out.blend> <x0>
#        env L=187 H=34 W=30 ANG=45 PL=1.6 RA=3 RT=3 RS=6 NS=5 NSB=3
import bpy, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, OX = a[0], float(a[1])
E = lambda k, d: float(os.environ.get(k, d))
L, H, W, ANG, PL, RA, RT, RS, NS, NSB = (E(k, d) for k, d in (("L", 187), ("H", 34), ("W", 30), ("ANG", 45), ("PL", 1.6), ("RA", 3),
                                                               ("RT", 3), ("RS", 6), ("NS", 5), ("NSB", 3)))
NS, NSB = int(NS), int(NSB); k = 1 / np.tan(np.radians(ANG)); YB = H * k
col = bpy.data.collections.get("GHIDAJ_R109") or bpy.data.collections.new("GHIDAJ_R109")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
def mat(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.diffuse_color = (*rgb, 1); return m
MP, MB, MS = mat("g_fin_profil", (.9, .3, .1)), mat("g_fin_baza", (.1, .5, .9)), mat("g_fin_sectiune", (.2, .8, .3))
def poly(name, P, m, closed=False):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.5; sp = cu.splines.new("POLY")
    sp.points.add(len(P) - 1)
    for p, q in zip(sp.points, P): p.co = (OX + q[0], q[1], q[2], 1)
    sp.use_cyclic_u = closed; o = bpy.data.objects.new(name, cu); o.data.materials.append(m); o.color = (*m.diffuse_color[:3], 1)
    col.objects.link(o); return o
def resample(P, step):
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; t = np.linspace(0, s[-1], max(2, int(s[-1] / step) + 1))
    return np.c_[tuple(np.interp(t, s, P[:, i]) for i in range(P.shape[1]))]
# spine: back edge centre, Bezier apex, leading edge
t = np.linspace(0, 1, 2000); lead = np.c_[t * L, H * (1 - t ** PL)]
# apex = a circular fillet of radius RA tangent to the back edge and to the leading edge (centre: RA inside the back edge, RA
# under the leading edge)
de = np.array([YB, -H]) / np.hypot(YB, H); nb = np.array([de[1], -de[0]])                       # back edge dir (down), inward normal
if nb[0] < 0: nb = -nb
cands = np.array([0, H]) + nb * RA + de[None, :] * np.linspace(0, 4 * RA, 4000)[:, None]
dl = np.array([np.min(np.hypot(*(lead - c).T)) for c in cands]); C0 = cands[np.argmin(np.abs(dl - RA))]
Tb = C0 - nb * RA; Tl = lead[np.argmin(np.hypot(*(lead - C0).T))]
a0, a1 = np.arctan2(*(Tb - C0)[::-1]), np.arctan2(*(Tl - C0)[::-1])
if a1 - a0 > np.pi: a1 -= 2 * np.pi                                                              # the short way round
if a0 - a1 > np.pi: a1 += 2 * np.pi
fil = np.array([C0 + RA * np.array([np.cos(q), np.sin(q)]) for q in np.linspace(a0, a1, 60)])
spine = resample(np.r_[np.c_[np.linspace(YB, Tb[0], 80), np.linspace(0, Tb[1], 80)][:-1], fil, lead[lead[:, 0] > Tl[0]]], 0.5)
poly("g_fin_A_profil", [(0, y, z) for y, z in spine], MP)
ia = int(np.argmax(spine[:, 1])); top = spine[ia:]; edge = spine[:ia + 1][::-1]                # y increasing on both
ztop = lambda y: np.interp(y, top[:, 0], top[:, 1])
# back face side edges (asked: g_fin_A_profil_spate_S/D and g_fin_A_profil all meet at the apex of g_fin_A_profil): they follow
# the spine's back edge in (y, z) from the base's back corners (+-W/2, YB, 0) up over the fillet to the apex, x tapering linearly
# with the arc length to 0 there, so the back face is a 45 deg triangle W wide at the base, closing at the apex
bp = spine[:ia + 1]; sb = np.r_[0, np.cumsum(np.linalg.norm(np.diff(bp, axis=0), axis=1))]; xe = W / 2 * (1 - sb / sb[-1])
kb = int(np.argmin(bp[:, 0])) + 1                                     # the straight part (y monotonic) for the ribs' lookups
we = lambda y: np.interp(y, bp[:kb][::-1, 0], xe[:kb][::-1]); zedge = lambda y: np.interp(y, bp[:kb][::-1, 0], bp[:kb][::-1, 1])
for sd, nm in ((-1, "S"), (1, "D")):
    poly("g_fin_A_profil_spate_%s" % nm, [(sd * x, y, z) for x, (y, z) in zip(xe, bp)], MP)
# base: isosceles triangle, front blunted by a circle radius RT tangent to the sides, nose at y = L
yc = L - RT; Pc = np.array([W / 2, YB]); C = np.array([0, yc]); dv = Pc - C; d = np.linalg.norm(dv)
th = np.arctan2(dv[1], dv[0]) + np.arccos(RT / d)                                              # tangent point, right side
T = C + RT * np.array([np.cos(th), np.sin(th)]); arc = np.array([C + RT * np.array([np.cos(a_), np.sin(a_)]) for a_ in np.linspace(th, np.pi - th, 41)])
right = resample(np.array([Pc, T]), 1.0); base = np.r_[right, arc[1:-1], (right * [-1, 1])[::-1]]
back = resample(np.array([[-W / 2, YB], [W / 2, YB]]), 1.0)[1:-1]; base = np.r_[base, back]
poly("g_fin_A_baza", [(x, y, 0) for x, y in base], MB, closed=True)
def half_w(y):                                                       # base half-width at y (sides + nose circle)
    if y <= T[1]: return W / 2 + (T[0] - W / 2) * (y - YB) / (T[1] - YB)
    return np.sqrt(max(RT ** 2 - (y - yc) ** 2, 0))
def rib(y, xb, zb, closed, zt=None):
    # spine radius RS, shrunk smoothly where the rib is too narrow for it: the largest r <= RS that keeps the corner (+-xb, zb) at
    # least 1.15 r from the circle's centre (asked: smooth the crease near the apex - a single arc through the corners bulged out
    # there, wider than the rib's own base, wherever the rib was taller than wide)
    zt = ztop(y) if zt is None else zt; hh = zt - zb; q = 1.15 ** 2 - 1
    R = min(RS, (-2 * hh + np.sqrt(4 * hh * hh + 4 * q * (xb * xb + hh * hh))) / (2 * q), 0.85 * xb); Cz = zt - R   # <= the rib's half-width: no bulge over its corners
    dv = np.array([xb, zb - Cz]); d = np.linalg.norm(dv); a0 = np.arctan2(dv[1], dv[0]) + np.arccos(R / d)
    side = resample(np.array([[-xb, zb], [-R * np.cos(a0), Cz + R * np.sin(a0)]]), 0.5)
    cap = [(R * np.cos(a_), Cz + R * np.sin(a_)) for a_ in np.linspace(np.pi - a0, a0, 61)]
    pts = list(map(tuple, side[:-1])) + cap + [(-x, z) for x, z in side[:-1][::-1]]
    if closed: pts += [(x, zb) for x in np.linspace(xb, -xb, int(2 * xb) + 2)[1:-1]]
    return [(x, y, z) for x, z in pts], R
RIBY = [YB + s * (L - YB) for s in np.linspace(.12, .88, NS)] + list(np.linspace(0, YB, NSB + 2)[1:-1])
for j, s in enumerate(np.linspace(.12, .88, NS)):
    y = YB + s * (L - YB); P, R = rib(y, half_w(y), 0.0, False); poly("g_fin_A_sectiune_%d" % j, P, MS)
    print("COASTA %d: y %.1f, latime baza %.1f, inaltime %.1f, raza spinare %.1f" % (j, y, 2 * half_w(y), ztop(y), R))
for j, y in enumerate(np.linspace(0, YB, NSB + 2)[1:-1]):
    xb = we(y); P, R = rib(y, xb, zedge(y), True); poly("g_fin_A_sectiune_spate_%d" % j, P, MS, closed=True)
    print("COASTA spate %d: y %.1f, latime fata spate %.1f, de la z %.1f la %.1f, raza spinare %.1f" % (j, y, 2 * xb, zedge(y), ztop(y), R))
print("VARF: rotunjit cu R %.1f, cel mai inalt punct z %.1f la y %.1f; tangent pe muchia din spate la y %.1f, pe bord la y %.1f" % (RA, top[0, 1], top[0, 0], Tb[0], Tl[0]))
print("GHIDAJ A2: baza triunghi y %.0f..%.0f, %.0f m lat in spate, nas R %.0f; fata din spate 45 grade, triunghi %.0f m lat, inchis in varf; varf %.0f m; raza spinare %.0f m"
      % (YB, L, W, RT, W, H, RS))
# env SUP=1 (asked: draw the surface): one closed solid lofted through sections in the planes y = const, every section built
# like the ribs (spine circle RS, tangent sides) between the profile's lower and upper crossing at that y; its bottom closed by
# the base (z = 0) in front of YB, by the 45 deg back face behind it. Where the back face wraps over the apex fillet (both
# crossings on the back edges' path) the section's top is widened by the back edges' half-width there, so g_fin_A_profil_spate_S/D
# lie on the surface up to the apex. Ends: a fan to the nose point in front, a fan to the last section's centre at the back.
if os.environ.get("SUP") == "1":
    import bmesh
    cs = np.r_[0, np.cumsum(np.linalg.norm(np.diff(spine, axis=0), axis=1))]
    xpath = lambda s_: max(0.0, W / 2 * (1 - s_ / sb[-1]))
    def cross(y):                                                   # [(z, s)] where the spine crosses the plane y
        out = []
        for i in range(len(spine) - 1):
            y0, y1_ = spine[i, 0], spine[i + 1, 0]
            if (y0 - y) * (y1_ - y) <= 0 and y0 != y1_:
                f = (y - y0) / (y1_ - y0); out.append((spine[i, 1] + f * (spine[i + 1, 1] - spine[i, 1]), cs[i] + f * (cs[i + 1] - cs[i])))
        return sorted(out)
    NH, NB_, NT = 40, 14, 4
    def rs(P, n):
        return resample(np.asarray(P), 1e9) if len(P) < 2 else np.c_[tuple(np.interp(np.linspace(0, 1, n), *(lambda c: (c / c[-1], ))(np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]), P[:, i]) for i in range(2))]
    def section(y):
        c = cross(y)
        if len(c) == 1 or y >= YB: zb, xb = 0.0, half_w(y)
        else: zb, xb = c[0][0], xpath(c[0][1])
        zt, su = c[-1]; xu = xpath(su) if su < sb[-1] else 0.0
        P, R = rib(y, xb - xu, zb, False, zt)
        m = len(P) // 2; left = np.array([(x, z) for x, _, z in P[:m + 1]])
        left = rs(left, NH); left[:, 0] -= xu * np.linspace(1, 1, NH)
        top = np.c_[np.linspace(-xu, xu, NT + 2)[1:-1], np.full(NT, zt)]
        right = (left * [-1, 1])[::-1]
        bot = np.c_[np.linspace(xb, -xb, NB_ + 2)[1:-1], np.full(NB_, zb)]
        return [(x, y, z) for x, z in np.r_[left, top, right, bot]]
    ymin = spine[:ia + 1, 0].min()
    ys = np.unique(np.round(np.r_[ymin + RA * (1 - np.cos(np.radians(np.linspace(0.5, 45, 40)))), ymin + RA * (1 - np.cos(np.radians(np.linspace(45, 90, 60)))), np.arange(top[0, 0], YB, 0.5), YB,
                                  np.arange(YB, L - 4, 1.0), np.linspace(L - 4, L - 0.1, 12), [r for r in RIBY]], 4))
    loops = [section(y) for y in ys]; n = len(loops[0])
    bm = bmesh.new(); vv = [[bm.verts.new((OX + x, y, z)) for x, y, z in lp] for lp in loops]
    for a_, b_ in zip(vv[:-1], vv[1:]):
        for i in range(n): bm.faces.new((a_[i], a_[(i + 1) % n], b_[(i + 1) % n], b_[i]))
    for a_, b_ in zip(vv[:-1], vv[1:]):                              # the bottom corners' lines = base / back face margins
        for i in (0, 2 * NH + NT - 1): bm.edges.get((a_[i], b_[i])).smooth = False
    kB = int(np.argmin(np.abs(ys - YB)))                              # the base's back edge (back face / base, 45 deg)
    for i in list(range(2 * NH + NT - 1, n)) + [0]: bm.edges.get((vv[kB][i], vv[kB][(i + 1) % n])).smooth = False
    cb = bm.verts.new(tuple(np.mean([v.co for v in vv[0]], axis=0))); nose = bm.verts.new((OX, L, 0))
    for i in range(n):
        bm.faces.new((cb, vv[0][(i + 1) % n], vv[0][i])); bm.faces.new((nose, vv[-1][i], vv[-1][(i + 1) % n]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # the apex zone: y-plane sections cut the fillet twice, leaving small steps on the back face where it wraps over it; relaxed
    # by Laplacian passes on the vertices behind y = top + 2 m (asked: smooth the small crease where the three guides meet)
    NN = int(E("NETED", 30)); fix = {v for e in bm.edges if not e.smooth for v in e.verts}   # margins stay on the guides
    for i in range(NN):                                             # tapered: the zone shrinks pass by pass -> no step at its end
        za = [v for v in bm.verts if v.co.y < top[0, 0] + 4 * (1 - i / NN) and v not in fix]
        bmesh.ops.smooth_vert(bm, verts=za, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    me = bpy.data.meshes.new("sup_fin_A"); bm.to_mesh(me); bm.free()
    for f in me.polygons: f.use_smooth = True
    ms = mat("sup_fin", (.72, .72, .75)); me.materials.append(ms); so = bpy.data.objects.new("sup_fin_A", me); so.color = (.72, .72, .75, 1)
    col.objects.link(so)
    print("SUPRAFATA: %d sectiuni, %d v, %d f" % (len(ys), len(me.vertices), len(me.polygons)))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
