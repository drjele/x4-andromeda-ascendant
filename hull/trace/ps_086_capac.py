# Component 086 as the lid of a room on the deck (asked): the plate at the reference plate's height and curvature (a
# smooth quadratic fitted to its top), its outline symmetric (half-width straight along y, front a parabola fitted on the
# reference edge, back straight); the walls on the left, right and back hang from the plate down to the body's flat floor;
# the front is open, closed by a comb of NT thin teeth (bars with rounded edges) hanging from the plate's front edge to
# the floor, evenly spaced (tooth to tooth = tooth to side). Plate, walls and teeth are separate objects (joined at the
# end). Built in ship coordinates (x + DX), moved by OFF (exploded view).
# Usage: blender -b <file.blend> --python ps_086_capac.py -- <esantion_punte.npz> <out.blend> <dx> <off>
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; S = np.load(a[0]); OUT, DX = a[1], float(a[2]); OFF = Vector([float(v) for v in a[3].split(",")])
env = lambda k, d: float(os.environ.get(k, d))
TP, WT, ZF = env("P086_GROSIME", "3"), env("P086_PERETE_GROS", "4"), env("P086_PODEA", "272")
SL = env("P086_PANTA", "22")                                            # how far the sloped outer wall runs out onto the body
CORP = np.load(os.environ["P086_CORP"]) if os.environ.get("P086_CORP") else None
def zbody(x, y):                                                        # the body's top surface (deck section data, |x|)
    if CORP is None: return ZF
    ys, s_, E, T = CORP["ys"], CORP["s"], CORP["edge"], CORP["top"]; k = int(np.clip(np.searchsorted(ys, y), 1, len(ys) - 1)); f = (y - ys[k - 1]) / (ys[k] - ys[k - 1])
    return (1 - f) * np.interp(abs(x), s_ * E[k - 1], T[k - 1]) + f * np.interp(abs(x), s_ * E[k], T[k])
NT, TWc, TDc = int(env("P086_DINTI", "5")), env("P086_DINTE_LAT", "6"), env("P086_DINTE_ADANC", "4")
q = S["p086"]; YB, YF = q[:, 1].min(), q[:, 1].max(); xc_ = (q[:, 0].min() + q[:, 0].max()) / 2
yy = np.arange(YB, YF, 4.0); hw = np.array([(abs(q[np.abs(q[:, 1] - y) < 2][:, 0].min()) + q[np.abs(q[:, 1] - y) < 2][:, 0].max()) / 2 for y in yy])
A_ = np.polyfit(yy[yy < YF - 40], hw[yy < YF - 40], 1); W = lambda y: np.polyval(A_, y); WF = W(YF)
fx = np.arange(-WF + 4, WF - 4, 4.0); fy = np.array([q[np.abs(q[:, 0] - xc_ - x) < 2][:, 1].max() for x in fx])
cF = float(np.linalg.lstsq((fx ** 2)[:, None], YF - fy, rcond=None)[0][0]); front = lambda x: YF - cF * x ** 2
# the lid's top: highest point per 4 m cell (centred on the plate), fitted by z = c0 + c1 y + c2 y^2 + c3 x^2 + c4 x^2 y
cx, cy_ = np.round((q[:, 0] - xc_) / 4).astype(int), np.round(q[:, 1] / 4).astype(int); top = {}
for x_, y_, z_ in zip(cx, cy_, q[:, 2]): top[(x_, y_)] = max(top.get((x_, y_), -1e9), z_)
P3 = np.array([(k[0] * 4.0, k[1] * 4.0, v) for k, v in top.items()]); X_, Y_ = P3[:, 0], P3[:, 1]
cz = np.linalg.lstsq(np.stack([np.ones_like(X_), Y_, Y_ ** 2, X_ ** 2, X_ ** 2 * Y_], 1), P3[:, 2], rcond=None)[0]
zl = lambda x, y: cz[0] + cz[1] * y + cz[2] * y ** 2 + cz[3] * x ** 2 + cz[4] * x ** 2 * y
if os.environ.get("P086_PLAT"):                                          # asked: the lid's top flat (level at its highest point)
    _zp = float(os.environ.get("P086_CAPAC_Z") or cz[0] + cz[1] * ((YB + YF) / 2) + cz[2] * ((YB + YF) / 2) ** 2); zl = lambda x, y: _zp + 0 * x
st = 1.0
back = [(x, YB) for x in np.arange(-W(YB), W(YB), st)]
right = [(W(y), y) for y in np.arange(YB, front(WF), st)]
fr = [(x, front(x)) for x in np.arange(WF, -WF, -st)]
left = [(-W(y), y) for y in np.arange(front(WF), YB, -st)]
P2 = np.array(back + right + fr + left); k_ = np.exp(-0.5 * (np.arange(-6, 7) / 2.0) ** 2); k_ /= k_.sum()
P2 = np.stack([np.convolve(np.r_[P2[-6:, i], P2[:, i], P2[:6, i]], k_, "valid") for i in range(2)], 1)
col = bpy.data.collections.get(os.environ.get("COLECTIE", "PS_NOU_EXPLODAT")) or bpy.data.collections.new(os.environ.get("COLECTIE", "PS_NOU_EXPLODAT"))
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
src = bpy.data.objects["R082 086_S"]; mat = src.material_slots[src.data.polygons[0].material_index].material
def obj(name, me):
    if name in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[name])
    me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = OFF; return o
def mesh(name, V, F):
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free(); return me
# plate
bm = bmesh.new(); vs = [bm.verts.new((x, y, 0)) for x, y in P2]; bm.faces.new(vs); bmesh.ops.triangulate(bm, faces=bm.faces[:])
for _ in range(8):
    long_ = [e for e in bm.edges if e.calc_length() > 3.0]
    if not long_: break
    bmesh.ops.subdivide_edges(bm, edges=long_, cuts=1, use_grid_fill=False); bmesh.ops.triangulate(bm, faces=bm.faces[:])
bmesh.ops.beautify_fill(bm, faces=bm.faces[:], edges=bm.edges[:])
for v in bm.verts: v.co.z = zl(v.co.x, v.co.y) - TP; v.co.x += DX
dup = bmesh.ops.duplicate(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:])
for v in [g for g in dup["geom"] if isinstance(g, bmesh.types.BMVert)]: v.co.z += TP
bmesh.ops.bridge_loops(bm, edges=[e for e in bm.edges if e.is_boundary]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
mep = bpy.data.meshes.new(os.environ.get("NUME_PREFIX", "comp_") + "086_capac"); bm.to_mesh(mep); bm.free()
if not os.environ.get("P086_DOAR_DINTI"): obj(os.environ.get("NUME_PREFIX", "comp_") + "086_capac", mep)   # the hood replaces lid + walls
# walls: left side -> back -> right side, set in by WT/2, from the floor up into the plate
path = np.array(left[::-1] + back + right); path = np.stack([np.convolve(np.r_[[path[0, i]] * 6, path[:, i], [path[-1, i]] * 6], k_, "valid") for i in range(2)], 1)
tg = np.gradient(path, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]; nrm = np.stack([tg[:, 1], -tg[:, 0]], 1)
V = []; NSL = 10
for p, n in zip(path, nrm):
    c = p - n * WT / 2; zt = zl(c[0], c[1]) - TP + 0.5; ring = [(-WT / 2, ZF - 1.0), (-WT / 2, zt)]
    foot = c + n * (WT / 2 + SL); zf = zbody(foot[0], foot[1]) - 0.3
    for t in np.linspace(0, 1, NSL + 1):                                  # steep at the plate, flat where it meets the body
        ring.append((WT / 2 + SL * (1 - np.cos(np.pi * t / 2)), zt + 0.5 - (zt + 0.5 - zf) * np.sin(np.pi * t / 2)))
    ring.append((WT / 2 + SL, ZF - 1.0))
    for u, z in ring: V.append((c[0] + n[0] * u + DX, c[1] + n[1] * u, z))
prof = ring
M, L = len(prof), len(path)
F = [(i * M + j, i * M + (j + 1) % M, (i + 1) * M + (j + 1) % M, (i + 1) * M + j) for i in range(L - 1) for j in range(M)] + [tuple(range(M))[::-1], tuple(range((L - 1) * M, L * M))]
if not os.environ.get("P086_DOAR_DINTI"): obj(os.environ.get("NUME_PREFIX", "comp_") + "086_pereti", mesh(os.environ.get("NUME_PREFIX", "comp_") + "086_pereti", V, F))
# comb: NT bars hanging from the front edge, rounded-rectangle section (superellipse), evenly spaced
NTUB, PAS, TW_, TH_, TL_ = int(env("P086_TUBURI", "3")), env("P086_TUB_PAS", "51.5"), 40.0, 30.0, 80.0
tc = (np.arange(NTUB) - (NTUB - 1) / 2) * PAS; wall_in = WF - WT                # tube centres, the room's inner side wall
cs = np.r_[(tc[:-1] + tc[1:]) / 2, [-(tc[-1] + TW_ / 2 + wall_in) / 2, (tc[-1] + TW_ / 2 + wall_in) / 2]] if NTUB else (np.arange(NT) - (NT - 1) / 2) * 2 * WF / (NT + 1)
cs = np.sort(cs); th = np.linspace(0, 2 * np.pi, 33)[:-1]
V, F = [], []
for c in cs:
    yc = front(c) - TDc / 2 - 0.5; zt = zl(c, yc) - TP + 0.5; base = len(V)
    ring = [(c + TWc / 2 * np.sign(np.cos(t)) * abs(np.cos(t)) ** 0.5, yc + TDc / 2 * np.sign(np.sin(t)) * abs(np.sin(t)) ** 0.5) for t in th]
    for z in np.linspace(ZF, zt, 12):
        for x, y in ring: V.append((x + DX, y, z))
    R_ = len(ring)
    F += [(base + i * R_ + j, base + i * R_ + (j + 1) % R_, base + (i + 1) * R_ + (j + 1) % R_, base + (i + 1) * R_ + j) for i in range(11) for j in range(R_)]
    F += [tuple(base + j for j in range(R_))[::-1], tuple(base + 11 * R_ + j for j in range(R_))]
obj(os.environ.get("NUME_PREFIX", "comp_") + "086_dinti", mesh(os.environ.get("NUME_PREFIX", "comp_") + "086_dinti", V, F))
mt = bpy.data.materials.get("tub_lansare") or bpy.data.materials.new("tub_lansare"); mt.diffuse_color = (0.35, 0.45, 0.6, 1)
for i, c in enumerate(tc):                                              # launch tube placeholders, door at the room's front
    yf = front(c) - 2.0; z0 = ZF + 1.0; bx = [(c - TW_ / 2, yf - TL_), (c + TW_ / 2, yf)]
    V = [(x + DX, y, z) for z in (z0, z0 + TH_) for x, y in ((bx[0][0], bx[0][1]), (bx[1][0], bx[0][1]), (bx[1][0], bx[1][1]), (bx[0][0], bx[1][1]))]
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    nm = "launchtube_s_%02d" % (i + 1)
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm])
    me = bpy.data.meshes.new(nm); me.from_pydata(V, [], F); me.materials.append(mt); o = bpy.data.objects.new(nm, me); col.objects.link(o); o.location = OFF
    o["x4_macro"] = "launchtube_arg_s_01_macro"; o["dimensiuni_m"] = "40 x 30 x 80 (lat x inalt x lung)"
for nm in (os.environ.get("NUME_PREFIX", "comp_") + "086_placa", os.environ.get("NUME_PREFIX", "comp_") + "086_pereti_v0", "echiv_R082 086_S"):
    o = bpy.data.objects.get(nm)
    if o:
        o.hide_render = True
        try: o.hide_set(True)
        except RuntimeError: pass                                       # in an excluded collection
print("TUBURI S: %d la x %s, usa la fata incaperii, podea z %.0f" % (NTUB, np.round(tc, 1).tolist(), ZF)); print("086 CAPAC: placa la z %.0f..%.0f (grosime %.0f), podea z %.0f -> incaperea %.0f..%.0f m inalta; pereti %.0f m; %d dinti de %.0f x %.0f m la x %s" % (zl(WF, YF), zl(0, (YB + YF) / 2), TP, ZF, zl(WF, YB) - TP - ZF, zl(0, (YB + YF) / 2) - TP - ZF, WT, NT, TWc, TDc, np.round(cs).astype(int).tolist()))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
