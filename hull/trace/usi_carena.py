# Doors in at_PS_carena in front of the blades (asked: the carena gets doors / segments where the blades and hinges go through it,
# pulled inwards towards its middle axis; the back set in 2 stacked segments). Per door (outline from usi_carena_contur.py):
#   door   = a solid block of the carena inside the outline shrunk DSEAM (outer wall straight at XD, under the arm's PS end), up to
#            the bay top - DSEAM - keeps the carena's UV / material; slides inwards like the arm doors (asked: carena solid)
#   bay    = the carena inside the outline (ends DSEAM past the notch ends) up to the footprint top + 1 m   -> cut out (past XD it
#            stays hidden under the arm and its closed door)
#   pocket = along x (the slide), floor / roof following the door's own profile along y, GT off the door                      -> cut out
# all walls are prisms over the outlines (clean lines).
# Path (object location, linear keys): rise UP, slide +x by the door's width (asked: in exactly their width, no deeper; the back door
# one piece); like at_usa_spate_D they close again behind the dropped blades (round hole R column + CL for the hinge, as the arm
# doors) and reopen before the blades climb back: 6-18 open, 44-56 closed, 106-118 open, 140-152 closed. S built, D the
# mirror (doors mirrored, cutters mirrored). Usage: blender -b <scene> --python usi_carena.py -- <contur.npz> <out.blend>
#   env DOORS=F,B XD=-60.1 DSEAM=.15 UP=1.5 GT=.4 CL=1 URMA=<urma_lame_carena npz>
import bpy, bmesh, sys, os, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree as BV
a = sys.argv[sys.argv.index("--") + 1:]; C_ = np.load(a[0]); OUT = a[1]; E = lambda k, d: os.environ.get(k, d)
DOORS = E("DOORS", "F,B").split(","); DSEAM, GT = (float(E(k, d)) for k, d in (("DSEAM", .15), ("GT", .4)))
XD = float(E("XD", -60.1))                                                # door outer edge: straight, just under the arm's flat PS end (x -59.6)
UPD = float(E("UP", 1.5)); CL = float(E("CL", 1.0))
FO, F = int(E("FO", 24)), int(E("F", 60))
sc = bpy.context.scene; sc.frame_set(1)
car = bpy.data.objects["at_PS_carena"]; OX = car.matrix_world.translation.copy(); col = bpy.data.collections["ATELIER_LAME"]
SL = dict(zip(C_["NUME"], C_["SL"]))
PAR = {k: C_["par_" + k] for k in C_["NUME"]}
def rbox(x0, x1, y0, y1, r_hi, r_lo, n=16):                               # x0 inner (larger x) side rounded: r_hi at y1, r_lo at y0
    P = []
    if r_hi > 0: P += [(x0 - r_hi + r_hi * math.cos(t), y1 - r_hi + r_hi * math.sin(t)) for t in np.linspace(0, math.pi / 2, n)]
    else: P += [(x0, y1)]
    P += [(x1, y1), (x1, y0)]
    if r_lo > 0: P += [(x0 - r_lo + r_lo * math.cos(t), y0 + r_lo + r_lo * math.sin(t)) for t in np.linspace(-math.pi / 2, 0, n)]
    else: P += [(x0, y0)]
    return P
def prism(name, poly, z0, z1):                                             # closed vertical prism over a CCW-or-CW polygon
    bm = bmesh.new(); lo = [bm.verts.new((x, y, z0)) for x, y in poly]; hi = [bm.verts.new((x, y, z1)) for x, y in poly]
    bm.faces.new(lo[::-1]); bm.faces.new(hi)
    for i in range(len(poly)): j = (i + 1) % len(poly); bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); return o
def boolean(obj, op, other):
    m = obj.modifiers.new("b", "BOOLEAN"); m.operation = op; m.object = other; m.solver = "EXACT"; bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); nm = bpy.data.meshes.new_from_object(obj.evaluated_get(dg)); obj.modifiers.remove(m); return nm
def apply(obj, op, other):
    nm = boolean(obj, op, other); old = obj.data; obj.data = nm; nm.name = old.name if old.users == 0 else nm.name
    if old.users == 0: bpy.data.meshes.remove(old)
def tmp_copy(o, name):
    c = bpy.data.objects.new(name, o.data.copy()); c.matrix_world = Matrix.Identity(4); sc.collection.objects.link(c); return c
def kill(*obs):
    for o in obs: me = o.data; bpy.data.objects.remove(o); (me.users == 0) and bpy.data.meshes.remove(me)
# --- carena in local (= ship) coords; skin heightfield (underside, ray from below)
def bvh(me): return BV.FromPolygons([v.co.copy() for v in me.vertices], [list(p.vertices) for p in me.polygons])
T0 = bvh(car.data)
# the carena is open where the arm's compartment walls close it: closed for the booleans with planar fills (triangle_fill per loop,
# winding from the neighbours), the fill faces dropped again after the cuts
bmc = bmesh.new(); bmc.from_mesh(car.data); NB0 = sum(1 for e in bmc.edges if e.is_boundary)
def bloops(bm):
    bd = [e for e in bm.edges if e.is_boundary]; adj = {}
    for e in bd:
        for v in e.verts: adj.setdefault(v, []).append(e)
    seen, out = set(), []
    for e0 in bd:
        if e0 in seen: continue
        L = []; st = [e0]; seen.add(e0)
        while st:
            e = st.pop(); L.append(e)
            for v in e.verts:
                for f in adj[v]:
                    if f not in seen: seen.add(f); st.append(f)
        out.append(L)
    return out
FV = []
for L in bloops(bmc):
    old_f = {e: e.link_faces[0] for e in L}; nf = [g for g in bmesh.ops.triangle_fill(bmc, use_beauty=True, use_dissolve=False, edges=L)["geom"] if isinstance(g, bmesh.types.BMFace)]
    seen_f, todo = set(), [f for f in nf if any(e in old_f for e in f.edges)]
    for f in todo:                                                         # seed: same edge direction as the old neighbour -> flip
        e = next(x for x in f.edges if x in old_f); lf = next(l for l in f.loops if l.edge == e); lo = next(l for l in old_f[e].loops if l.edge == e)
        if lf.vert == lo.vert: f.normal_flip()
        seen_f.add(f)
    nfs = set(nf); st = list(seen_f)
    while st:                                                              # propagate consistent winding over the fill
        f = st.pop()
        for e in f.edges:
            for g in e.link_faces:
                if g in nfs and g not in seen_f:
                    lf = next(l for l in f.loops if l.edge == e); lg = next(l for l in g.loops if l.edge == e)
                    if lf.vert == lg.vert: g.normal_flip()
                    seen_f.add(g); st.append(g)
    FV += [[v.co.copy() for v in f.verts] for f in nf]
TF = BV.FromPolygons([p for t in FV for p in t], [[3 * i, 3 * i + 1, 3 * i + 2] for i in range(len(FV))])
closed = bpy.data.meshes.new("tmp_carena_inchisa"); bmc.to_mesh(closed); NBC = sum(1 for e in bmc.edges if e.is_boundary); bmc.free()
orig_me = car.data; ORIG_NAME = orig_me.name; car.data = closed
for mt in orig_me.materials: closed.materials.append(mt)              # bmesh.to_mesh does not carry the material slots
print("USA_CARENA carena inchisa temporar: %d muchii libere -> %d (%d triunghiuri de umplere)" % (NB0, NBC, len(FV)))
SETOF = {"F": "fata", "B": "spate"}
U_ = np.load(E("URMA", "/home/adrian/Documents/Andromeda/2026-10-29-imbinari/piese/urma_lame_carena_v1.npz")); ZMAX = {s_: U_[s_][:, 2].max() for s_ in ("fata", "spate")}
doorsS, cutters, ZTOP = {}, [], {}
for k in DOORS:
    x0, x1, y0, y1, rc = PAR[k]; zc = ZMAX[SETOF[k]] + 1.0
    hole = rbox(x0, x1, y0 - DSEAM, y1 + DSEAM, rc, rc)
    dpol = rbox(x0 - DSEAM, XD, y0, y1, rc - DSEAM, rc - DSEAM)
    # door: a solid block of the carena inside the door outline, up to the bay top (asked: the carena solid, no hollowed look;
    # a straight wall sliding inwards like the arm doors in the arms, the other way)
    pd = prism("tmp_pd", dpol, 240, zc - DSEAM); cc = tmp_copy(car, "tmp_cc"); dm = boolean(cc, "INTERSECT", pd); kill(pd); bpy.data.objects.remove(cc)
    dm.name = "at_usa_carena_%s_S" % k; bd = bmesh.new(); bd.from_mesh(dm); nfree = sum(1 for e in bd.edges if e.is_boundary); bd.free()
    if not dm.materials:
        for mt in car.data.materials: dm.materials.append(mt)
    door = bpy.data.objects.new(dm.name, dm); doorsS[k] = door; col.objects.link(door); door.location = OX
    col_ = bpy.data.objects["at_spinare_%s_S" % SETOF[k]]; ccx, ccy = col_.matrix_world.translation.x - OX.x, col_.matrix_world.translation.y   # the hinge
    rcol = max(v.co.xy.length for v in col_.data.vertices) * col_.matrix_world.to_scale().x + CL     # stays down through the closed door: same hole as the arm doors
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=rcol, depth=200, location=(ccx, ccy, 270)); cyl = bpy.context.active_object; tdoor = tmp_copy(door, "tmp_door")
    for ye in (y0, y1):                                                   # hole close to a door end: open it to the end (no thin sliver left)
        if abs(ccy - ye) < rcol + 2.0:
            ext = prism("tmp_ext", rbox(ccx + rcol, ccx - rcol, min(ccy, ye - 1), max(ccy, ye + 1), 0, 0), 170, 370)
            cyl.data = boolean(cyl, "UNION", ext); kill(ext)
    nm = boolean(tdoor, "DIFFERENCE", cyl); dm.clear_geometry(); bx = bmesh.new(); bx.from_mesh(nm); bx.to_mesh(dm); bx.free(); bpy.data.meshes.remove(nm); kill(cyl, tdoor)
    ztop_door = max(v.co.z for v in dm.vertices); zb = min(v.co.z for v in dm.vertices)
    # bay: the carena inside the hole outline up to the footprint's top + 1 m (flat ceiling)
    cutters.append(prism("tmp_bay_" + k, hole, 240, zc))
    # pocket: the door's path (raised UP, then inwards SL), flat floor / ceiling GT off the door
    up = UPD; zf, zt = 257.0 + up - GT, ztop_door + up + GT
    tD = bvh(dm); ys_ = np.arange(y0 - GT, y1 + GT + 1e-6, .25); fl, ce = [], []      # floor / roof follow the door's profile along y
    for y in ys_:                                                          # (the back end steps up to z 265.7: a flat floor broke the skin)
        b_, t_ = [], []
        for x in np.arange(XD, x0 - DSEAM + 1e-6, .5):
            for yy in (y - GT, y, y + GT):
                r = tD.ray_cast(Vector((x, yy, 200)), Vector((0, 0, 1)));  b_ += [r[0].z] if r[0] else []
                r = tD.ray_cast(Vector((x, yy, 400)), Vector((0, 0, -1))); t_ += [r[0].z] if r[0] else []
        fl.append(min(b_) + up - GT if b_ else np.nan); ce.append(max(t_) + up + GT if t_ else np.nan)
    fl = np.array(fl); ce = np.array(ce); ok = ~np.isnan(fl); fl = np.interp(ys_, ys_[ok], fl[ok]); ce = np.interp(ys_, ys_[ok], ce[ok])
    prof = [(y, z) for y, z in zip(ys_, fl)] + [(y, z) for y, z in zip(ys_[::-1], ce[::-1])]
    xa, xb = x0 - DSEAM + SL[k] + GT, x1; bm_ = bmesh.new(); A = [bm_.verts.new((xa, y, z)) for y, z in prof]; B_ = [bm_.verts.new((xb, y, z)) for y, z in prof]
    bm_.faces.new(A); bm_.faces.new(B_[::-1])
    for i in range(len(prof)): j = (i + 1) % len(prof); bm_.faces.new((A[i], B_[i], B_[j], A[j]))
    bmesh.ops.recalc_face_normals(bm_, faces=bm_.faces); tm_ = bpy.data.meshes.new("tmp_tun_" + k); bm_.to_mesh(tm_); bm_.free()
    to_ = bpy.data.objects.new("tmp_tun_" + k, tm_); sc.collection.objects.link(to_); cutters.append(to_); zf, zt = fl.min(), ce.max()
    ZTOP[k] = ztop_door
    print("USA_CARENA %s: usa %d fete (libere %d), z %.1f..%.1f; gol pana la z %.1f; buzunar z %.1f..%.1f, x pana la %.1f, y %.1f..%.1f" % (
        k, len(dm.polygons), nfree, zb, ztop_door, zc, zf, zt, x0 + SL[k], y0, y1))
# --- D: mirror cutters and doors; cut everything out of the carena
def mirror_obj(o, name):
    me = o.data.copy(); bm = bmesh.new(); bm.from_mesh(me)
    for v in bm.verts: v.co.x = -v.co.x
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free(); m = bpy.data.objects.new(name, me); me.name = name; return m
for c in list(cutters): m = mirror_obj(c, c.name + "_D"); sc.collection.objects.link(m); cutters.append(m)
n0 = len(car.data.polygons); cut = cutters[0]
for i_, c in enumerate(cutters[1:]): cut.data = boolean(cut, "UNION", c); print("UNIRE %d %s" % (i_, c.name), flush=True)
cl = tmp_copy(car, "tmp_car"); newme = boolean(cl, "DIFFERENCE", cut); car.data = newme; bpy.data.objects.remove(cl)
for c in cutters: kill(c)
bm = bmesh.new(); bm.from_mesh(car.data)                                 # reopen: what is left of the fill faces goes
dead = [f for f in bm.faces if (lambda r: r[0] is not None and r[3] < 2e-3 and abs(r[1].dot(f.normal)) > .99)(TF.find_nearest(f.calc_center_median()))]
bmesh.ops.delete(bm, geom=dead, context="FACES"); NB1 = sum(1 for e in bm.edges if e.is_boundary); bm.to_mesh(car.data); bm.free()
for m_ in (closed, orig_me):
    if m_.users == 0: bpy.data.meshes.remove(m_)
car.data.name = ORIG_NAME
print("USA_CARENA carena redeschisa: %d fete de umplere scoase; muchii libere %d -> %d" % (len(dead), NB0, NB1))
doorsD = {}
for k, d in doorsS.items():
    m = mirror_obj(d, d.name[:-2] + "_D"); col.objects.link(m); m.location = OX; doorsD[k] = m
# --- new carena faces: box UV, sharp > 30 deg; doors: sharp rims
def finish(me, ref_tree):
    bm = bmesh.new(); bm.from_mesh(me); uvl = bm.loops.layers.uv.active; newf = [f for f in bm.faces if (lambda r: r[0] is None or r[3] > 2e-3)(ref_tree.find_nearest(f.calc_center_median()))]
    for f in newf:
        f.smooth = True
        if uvl:
            ax = max(range(3), key=lambda q: abs(f.normal[q])); i, j = [(1, 2), (0, 2), (0, 1)][ax]
            for lp in f.loops: lp[uvl].uv = (lp.vert.co[i] / 256.0, lp.vert.co[j] / 256.0)
    for e in {e for f in newf for e in f.edges}:
        e.smooth = not (len(e.link_faces) != 2 or e.calc_face_angle(0) > math.radians(30))
    bm.to_mesh(me); bm.free(); return len(newf)
nn = finish(car.data, T0)
for d in list(doorsS.values()) + list(doorsD.values()): finish(d.data, T0)
print("USA_CARENA carena: %d -> %d fete, %d fete noi (pereti gol / tunel)" % (n0, len(car.data.polygons), nn))
# --- animation (object location, linear)
def key(o, fr, off):
    o.location = OX + Vector(off); o.keyframe_insert("location", frame=fr)
def path_keys(k, mir):                                                    # like the arm doors: open, closed while the blades are out, open, closed
    sx = -1 if mir else 1; up = UPD; o, u, z = (sx * SL[k], 0, up), (0, 0, up), (0, 0, 0)
    seq = [(1, z), (6, z), (9, u), (18, o),                               # opens once the arm door has left the PS end, done before the blades come
           (44, o), (53, u), (56, z),                                     # closes behind the dropped blades (the hinge stays in its hole)
           (106, z), (109, u), (118, o),                                  # opens again before they climb back
           (140, o), (149, u), (152, z)]                                  # closes once they are in, before the arm door returns
    rev = []
    return seq + rev
for k in DOORS:
    for o, mir in ((doorsS[k], False), (doorsD[k], True)):
        o.animation_data_clear()
        for fr, off in path_keys(k, mir): key(o, fr, off)
        for fc in o.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
        print("USA_CARENA %s: chei %s" % (o.name, ", ".join("%d" % fr for fr, _ in path_keys(k, mir))))
sc.frame_set(1)
if not int(E("NOSAVE", 0)): bpy.ops.wm.save_as_mainfile(filepath=OUT)
