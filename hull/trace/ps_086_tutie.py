# Component 086 as ONE piece, a hood (asked: lid and walls one piece, the sloped outer walls moulded onto the body): an
# outer solid whose top is the lid (the reference plate's height and curvature) and, beyond the lid's outline on the left,
# back and right, a skirt with a quarter-circle profile (vertical at the lid's edge, lying down tangent onto the body's
# top surface SL m out); its bottom inside the body. The room is subtracted (exact boolean): under the lid, inside the
# walls (WT thick), down through the floor, open at the front. Outline, lid fit as ps_086_capac.py. Ship coordinates.
# Usage: blender -b <file.blend> --python ps_086_tutie.py -- <esantion_punte.npz> <corp.npz> <out.blend> <dx> [name]
import bpy, bmesh, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; S = np.load(a[0]); B = np.load(a[1]); OUT, DX = a[2], float(a[3]); NAME = a[4] if len(a) > 4 else "piesa_comp_086_tutie"
env = lambda k, d: float(os.environ.get(k, d))
TP, WT, ZF, SL = env("P086_GROSIME", "3"), env("P086_PERETE_GROS", "4"), env("P086_PODEA", "262"), env("P086_PANTA", "22")
q = S["p086"]; YB, YF = q[:, 1].min(), q[:, 1].max(); xc_ = (q[:, 0].min() + q[:, 0].max()) / 2
yy = np.arange(YB, YF, 4.0); hw = np.array([(abs(q[np.abs(q[:, 1] - y) < 2][:, 0].min()) + q[np.abs(q[:, 1] - y) < 2][:, 0].max()) / 2 for y in yy])
A_ = np.polyfit(yy[yy < YF - 40], hw[yy < YF - 40], 1); W = lambda y: np.polyval(A_, y); WF = W(YF)
fx = np.arange(-WF + 4, WF - 4, 4.0); fy = np.array([q[np.abs(q[:, 0] - xc_ - x) < 2][:, 1].max() for x in fx])
cF = float(np.linalg.lstsq((fx ** 2)[:, None], YF - fy, rcond=None)[0][0]); front = lambda x: YF - cF * x ** 2
cx, cy_ = np.round((q[:, 0] - xc_) / 4).astype(int), np.round(q[:, 1] / 4).astype(int); top = {}
for x_, y_, z_ in zip(cx, cy_, q[:, 2]): top[(x_, y_)] = max(top.get((x_, y_), -1e9), z_)
P3 = np.array([(k[0] * 4.0, k[1] * 4.0, v) for k, v in top.items()]); X_, Y_ = P3[:, 0], P3[:, 1]
cz = np.linalg.lstsq(np.stack([np.ones_like(X_), Y_, Y_ ** 2, X_ ** 2, X_ ** 2 * Y_], 1), P3[:, 2], rcond=None)[0]
zl = lambda x, y: cz[0] + cz[1] * y + cz[2] * y ** 2 + cz[3] * x ** 2 + cz[4] * x ** 2 * y
if os.environ.get("P086_PLAT"):                                          # asked: the lid's top flat (level at its highest point)
    _zp = float(os.environ.get("P086_CAPAC_Z") or cz[0] + cz[1] * ((YB + YF) / 2) + cz[2] * ((YB + YF) / 2) ** 2); zl = lambda x, y: _zp + 0 * x
ys, s_, E, T = B["ys"], B["s"], B["edge"], B["top"]
def zb(x, y):
    k = int(np.clip(np.searchsorted(ys, y), 1, len(ys) - 1)); f = (y - ys[k - 1]) / (ys[k] - ys[k - 1])
    return (1 - f) * np.interp(abs(x), s_ * E[k - 1], T[k - 1]) + f * np.interp(abs(x), s_ * E[k], T[k])
st = 1.0; k_ = np.exp(-0.5 * (np.arange(-6, 7) / 2.0) ** 2); k_ /= k_.sum()
yc0 = front(WF)
U = np.array([(-W(y), y) for y in np.arange(yc0, YB, -st)] + [(x, YB) for x in np.arange(-W(YB), W(YB), st)] + [(W(y), y) for y in np.arange(YB, yc0 + st, st)])
U = np.stack([np.convolve(np.r_[[U[0, i]] * 6, U[:, i], [U[-1, i]] * 6], k_, "valid") for i in range(2)], 1)   # left -> back -> right
tg = np.gradient(U, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]; NR = np.stack([tg[:, 1], -tg[:, 0]], 1)   # outward
FR = np.array([(x, front(x)) for x in np.arange(U[-1, 0], U[0, 0], -st)])  # front edge, right -> left
def solid(poly, ztop, zbot, maxe):                                      # 2-D polygon -> closed solid between two height fields
    bm = bmesh.new(); vs = [bm.verts.new((x, y, 0)) for x, y in poly]; bm.faces.new(vs); bmesh.ops.triangulate(bm, faces=bm.faces[:])
    for _ in range(10):
        long_ = [e for e in bm.edges if e.calc_length() > maxe]
        if not long_: break
        bmesh.ops.subdivide_edges(bm, edges=long_, cuts=1, use_grid_fill=False); bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.beautify_fill(bm, faces=bm.faces[:], edges=bm.edges[:])
    for v in bm.verts: v.co.z = zbot(v.co.x, v.co.y)
    dup = bmesh.ops.duplicate(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:])
    for v in [g for g in dup["geom"] if isinstance(g, bmesh.types.BMVert)]: v.co.z = ztop(v.co.x, v.co.y)
    bmesh.ops.bridge_loops(bm, edges=[e for e in bm.edges if e.is_boundary]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for v in bm.verts: v.co.x += DX
    return bm
# no boolean (the exact solver gave nothing, the fast one a non-manifold mess): the hood is built from two parts that share
# one rim and are welded there - a swept band along the U (inner wall face from the floor to the lid's underside, the lid's
# top across the wall, then the quarter-circle skirt down onto the body, closed underneath inside the body) and the lid
# plate whose outline is exactly the band's inner top edge (same points); the two faces lying on that shared rim removed
IN = U - NR * WT; NSK = 16; ring = []
for p, n, pi in zip(U, NR, IN):
    zi, zo = zl(pi[0], pi[1]), zl(p[0], p[1]); prof = [(-WT, ZF - 1.0), (-WT, zi - TP), (-WT, zi), (0.0, zo)]
    # skirt (organic): a blend lid -> body, (1 - g) body + g lid, rounding over from the lid and landing on the body
    for t in np.linspace(0, 1, NSK + 1)[1:]:                            # tangent to its real slope (g(1) = g'(1) = 0)
        d = SL * t; g = (1 - t ** 2) ** 2 if os.environ.get("P086_FUSTA_ORGANICA") else None
        prof.append((d, (1 - g) * (zb(*(p + n * d)) - 0.3) + g * zo) if g is not None else (d, zo - (zo - (zb(*(p + n * d)) - 0.3)) * np.sqrt(max(1 - (1 - t) ** 2, 0.0))))
    prof.append((SL, ZF - 1.0)); ring.append([(p[0] + n[0] * u + DX, p[1] + n[1] * u, z) for u, z in prof])
M_ = len(ring[0]); L_ = len(ring); V = [v for r in ring for v in r]
F = [(i * M_ + j, i * M_ + (j + 1) % M_, (i + 1) * M_ + (j + 1) % M_, (i + 1) * M_ + j) for i in range(L_ - 1) for j in range(M_) if j != 1]   # j = 1: the shared rim
F += [tuple(range(M_))[::-1], tuple(range((L_ - 1) * M_, L_ * M_))]
FRi = np.array([(x, front(x)) for x in np.linspace(IN[-1, 0], IN[0, 0], max(int(abs(IN[-1, 0] - IN[0, 0]) / st), 2))[1:-1]])
poly = np.vstack([IN, FRi]); nb = len(IN)
bm = bmesh.new(); vs = [bm.verts.new((x, y, 0)) for x, y in poly]; bm.faces.new(vs); bmesh.ops.triangulate(bm, faces=bm.faces[:])
for _ in range(10):
    long_ = [e for e in bm.edges if e.calc_length() > 3.0 and not e.is_boundary]
    if not long_: break
    bmesh.ops.subdivide_edges(bm, edges=long_, cuts=1, use_grid_fill=False); bmesh.ops.triangulate(bm, faces=bm.faces[:])
bmesh.ops.beautify_fill(bm, faces=bm.faces[:], edges=[e for e in bm.edges if not e.is_boundary])
for v in bm.verts: v.co.z = zl(v.co.x, v.co.y) - TP
dup = bmesh.ops.duplicate(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:])
for v in [g for g in dup["geom"] if isinstance(g, bmesh.types.BMVert)]: v.co.z += TP
rim = bmesh.ops.bridge_loops(bm, edges=[e for e in bm.edges if e.is_boundary])["faces"]
onU = lambda f: all(min(np.hypot(IN[:, 0] - v.co.x, IN[:, 1] - v.co.y)) < 1e-3 for v in f.verts)
bmesh.ops.delete(bm, geom=[f for f in rim if onU(f)], context="FACES")   # the plate's rim along the walls: shared with the band
for v in bm.verts: v.co.x += DX
base = len(bm.verts); bm.verts.ensure_lookup_table()
nv = [bm.verts.new(v) for v in V]
for f in F: bm.faces.new([nv[i] for i in f])
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-3); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
for nm in (NAME,):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm])
meA = bpy.data.meshes.new(NAME); bm.to_mesh(meA); bm.free()
col = bpy.data.collections.get(os.environ.get("COLECTIE", "PS_PIESE")) or bpy.data.collections.new(os.environ.get("COLECTIE", "PS_PIESE"))
oA = bpy.data.objects.new(NAME, meA); col.objects.link(oA)
src = bpy.data.objects["R082 086_S"]; meA.materials.append(src.material_slots[src.data.polygons[0].material_index].material)
for p in meA.polygons: p.use_smooth = True
bm = bmesh.new(); bm.from_mesh(meA); bnd = sum(1 for e in bm.edges if e.is_boundary); nm_ = sum(1 for e in bm.edges if len(e.link_faces) > 2); bm.free()
for old in ("piesa_comp_086_capac", "piesa_comp_086_pereti"):
    o = bpy.data.objects.get(old)
    if o:
        o.hide_render = True
        try: o.hide_set(True)
        except RuntimeError: pass
print("086 TUTIE: %d varfuri, %d fete, muchii libere %d, nemanifold %d; fusta %.0f m pe corp, pereti %.0f m, placa %.0f m, podea z %.0f" % (len(meA.vertices), len(meA.polygons), bnd, nm_, SL, WT, TP, ZF))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
