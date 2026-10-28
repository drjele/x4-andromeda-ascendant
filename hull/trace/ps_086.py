# Component 086 rebuilt as a scoop (U shape) on the deck: a plate lying on the body's top surface (from the deck
# envelope), its outline from the reference plate made symmetric and smooth (half-width a straight fit along y, the front
# edge a parabola through the rounded front corners); low walls with a rounded top along the left, right and back edges;
# at the front a comb of 3 teeth, evenly spaced across the width, rounded tips. Plate and walls are separate objects
# (to be joined at the end). Built in ship coordinates (x + DX), then moved by OFF (the exploded view).
# Usage: blender -b <file.blend> --python ps_086.py -- <punte_corp.npz> <esantion_punte.npz> <out.blend> <dx> <off_x,off_y,off_z>
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; N = np.load(a[0]); S = np.load(a[1]); OUT, DX = a[2], float(a[3]); OFF = Vector([float(v) for v in a[4].split(",")])
env = lambda k, d: float(os.environ.get(k, d))
TP, WT, WH, GAP = env("P086_GROSIME", "3"), env("P086_PERETE_GROS", "4"), env("P086_PERETE_H", "8"), env("P086_JOC", "0.5")
NT, TW, TL = 3, env("P086_DINTE_LAT", "18"), env("P086_DINTE_LUNG", "30")
q = S["p086"]; YB, YF = q[:, 1].min(), q[:, 1].max()
ys_ = np.arange(YB, YF, 4.0); hw = np.array([(abs(q[np.abs(q[:, 1] - y) < 2][:, 0].min()) + q[np.abs(q[:, 1] - y) < 2][:, 0].max()) / 2 for y in ys_])
A_ = np.polyfit(ys_[ys_ < YF - 40], hw[ys_ < YF - 40], 1); W = lambda y: np.polyval(A_, y)   # half-width, straight
WF = W(YF); xc_ = (q[:, 0].min() + q[:, 0].max()) / 2                    # the reference plate sits ~6 m off centre
fx = np.arange(-WF + 4, WF - 4, 4.0); fy = np.array([q[np.abs(q[:, 0] - xc_ - x) < 2][:, 1].max() for x in fx])
cF = float(np.linalg.lstsq((fx ** 2)[:, None], YF - fy, rcond=None)[0][0])   # front edge: y = YF - cF x^2, fitted on the whole edge
def ztop(x, y):                                                         # the body's top surface (deck envelope), |x| symmetric
    ys, s, E, X0, T = N["ys"], N["s"], N["edge"], N["x0"], N["top"]; k = np.clip(np.searchsorted(ys, y), 1, len(ys) - 1); f = (y - ys[k - 1]) / (ys[k] - ys[k - 1])
    zz = [np.interp(abs(x), X0[j] + s * (E[j] - X0[j]), T[j]) for j in (k - 1, k)]; return (1 - f) * zz[0] + f * zz[1]
# outline (counter-clockwise from the back-left corner): back edge, right side, front with the comb, left side
def front(x):                                                           # front edge + teeth (superellipse tips)
    y = YF - cF * x ** 2; cs = (np.arange(NT) - (NT - 1) / 2) * 2 * WF / (NT + 1)   # equal gaps: tooth to tooth = tooth to edge
    for c in cs:
        u = (x - c) / (TW / 2)
        if abs(u) < 1: y += TL * (1 - abs(u) ** 4) ** 0.25
    return y
st = 1.0; yb = YB + 0.0
back = [(x, yb) for x in np.arange(-W(yb), W(yb), st)]
right = [(W(y), y) for y in np.arange(yb, YF - cF * WF ** 2, st)]
fr = [(x, front(x)) for x in np.arange(WF, -WF, -st / 4)]
left = [(-W(y), y) for y in np.arange(YF - cF * WF ** 2, yb, -st)]
P2 = np.array(back + right + fr + left)
k_ = np.exp(-0.5 * (np.arange(-6, 7) / 2.0) ** 2); k_ /= k_.sum()       # small fillets: the outline smoothed around
P2 = np.stack([np.convolve(np.r_[P2[-6:, i], P2[:, i], P2[:6, i]], k_, "valid") for i in range(2)], 1)
col = bpy.data.collections.get("PS_NOU_EXPLODAT") or bpy.data.collections.new("PS_NOU_EXPLODAT")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
def obj(name, me):
    if name in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[name])
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = OFF
    src = bpy.data.objects.get("R082 086_S")
    if src:
        for m in src.data.materials: me.materials.append(m)
        mi = [p.material_index for p in src.data.polygons][0]
        for p in me.polygons: p.material_index = mi; p.use_smooth = True
    return o
# plate: the outline filled, subdivided to <= 3 m edges, laid on the body (+GAP), thickness TP
bm = bmesh.new(); vs = [bm.verts.new((x, y, 0)) for x, y in P2]; bm.faces.new(vs)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
for _ in range(8):
    long_ = [e for e in bm.edges if e.calc_length() > 3.0]
    if not long_: break
    bmesh.ops.subdivide_edges(bm, edges=long_, cuts=1, use_grid_fill=False); bmesh.ops.triangulate(bm, faces=bm.faces[:])
bmesh.ops.beautify_fill(bm, faces=bm.faces[:], edges=bm.edges[:])
for v in bm.verts: v.co.z = ztop(v.co.x, v.co.y) + GAP; v.co.x += DX
top = bmesh.ops.duplicate(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:])
for v in [g for g in top["geom"] if isinstance(g, bmesh.types.BMVert)]: v.co.z += TP
bnd = [e for e in bm.edges if e.is_boundary]
mep = bpy.data.meshes.new("comp_086_placa"); bm.to_mesh(mep); bm.free()
# side band joining the plate's top and bottom outlines (the plate's rim)
bm = bmesh.new(); bm.from_mesh(mep); bm.verts.ensure_lookup_table()
bot_loop = [e for e in bm.edges if e.is_boundary]; bmesh.ops.bridge_loops(bm, edges=bot_loop)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(mep); bm.free()
pl = obj("comp_086_placa", mep)
# walls: a rounded-top band swept along the left side, the back and the right side, set in by WT/2 from the outline
path = np.array(left[::-1][:-1] + back + right)                          # front-left -> back -> front-right
path = np.stack([np.convolve(np.r_[[path[0, i]] * 6, path[:, i], [path[-1, i]] * 6], k_, "valid") for i in range(2)], 1)
tg = np.gradient(path, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]; nrm = np.stack([tg[:, 1], -tg[:, 0]], 1)   # outward
th = np.linspace(0, np.pi, 13); prof = [(-WT / 2, 0.0)] + [(-WT / 2 * np.cos(t), WH - WT / 2 + WT / 2 * np.sin(t)) for t in th] + [(WT / 2, 0.0)]
V, F = [], []
for i, (p, n) in enumerate(zip(path, nrm)):
    c = p - n * WT / 2; zb = ztop(c[0], c[1]) + GAP + TP
    for (u, h) in prof: V.append((c[0] + n[0] * u + DX, c[1] + n[1] * u, zb + h))
M = len(prof); L = len(path)
F = [(i * M + j, i * M + j + 1, (i + 1) * M + j + 1, (i + 1) * M + j) for i in range(L - 1) for j in range(M - 1)]
F += [((i + 1) * M - 1, i * M, (i + 1) * M, (i + 2) * M - 1) for i in range(L - 1)]   # underside
F += [tuple(range(M))[::-1], tuple(range((L - 1) * M, L * M))]           # end caps
mew = bpy.data.meshes.new("comp_086_pereti"); mew.from_pydata(V, [], F)
bm = bmesh.new(); bm.from_mesh(mew); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(mew); bm.free()
pw = obj("comp_086_pereti", mew)
for nm in ("echiv_R082 086_S",):
    o = bpy.data.objects.get(nm)
    if o: o.hide_set(True); o.hide_render = True
print("086: latime %.0f..%.0f m, lungime %.0f m, fata y=YF-%.4f x^2, dinti %d x %.0f m lat, %.0f m lung; perete %.0f x %.0f m; placa %.0f m" % (2 * W(YB), 2 * WF, YF - YB, cF, NT, TW, TL, WT, WH, TP))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
