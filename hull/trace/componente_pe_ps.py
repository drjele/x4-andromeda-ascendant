# The PS components fitted to the new PS (asked: hood narrower - as far as the 3 hangars allow; belly V with its top = PS's flat
# bottom; 103_118 smoothed and carried down to PS; 055 sitting on PS - not floating, not sunk): in ship coordinates (built at
# DX = -1700, the new pieces at XN centred). The hood scaled in x by HOOD about the middle; the belly's mesh replaced by
# burta_noua.py's; 055 / 103_118 laid on the new body (PS + arms): over a 2 m grid seen from above, each column's lowest
# point moved onto the new surface below (vertical ray), the moves filled where the body is absent (nearest) and smoothed
# (gaussian SG m), every vertex moved by its column's value; 103_118 smoothed afterwards (Taubin). Reports the gaps.
# Usage: blender -b <f.blend> --python componente_pe_ps.py -- <out.blend> <burta_noua.npz> [hood_scale] [sg] [tube_pitch]
import bpy, bmesh, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT, BN = a[0], np.load(a[1]); HOOD = float(a[2]) if len(a) > 2 else 0.64; SG = float(a[3]) if len(a) > 3 else 8.0
DX = -1700.0; XN = bpy.data.objects["piesa_169_C_PS"].location.x
bm = bmesh.new()
for n in ("piesa_169_C_PS", "piesa_169_C_brat_D", "piesa_169_C_brat_S"):
    t = bmesh.new(); t.from_mesh(bpy.data.objects[n].data); m_ = bpy.data.meshes.new("t"); t.to_mesh(m_); t.free(); bm.from_mesh(m_); bpy.data.meshes.remove(m_)
bmesh.ops.translate(bm, verts=bm.verts, vec=(DX, 0, 0)); tree = BVHTree.FromBMesh(bm)   # the new body in the components' frame
def surf(x, y):
    h = tree.ray_cast(Vector((x, y, 800.0)), Vector((0, 0, -1.0)), 2000.0); return h[0].z if h[0] is not None else np.nan
def gauss2(A, s):
    n = int(3 * s); k = np.exp(-0.5 * (np.arange(-n, n + 1) / s) ** 2); k /= k.sum()
    A = np.apply_along_axis(lambda r: np.convolve(np.pad(r, n, mode="edge"), k, "valid"), 0, A); return np.apply_along_axis(lambda r: np.convolve(np.pad(r, n, mode="edge"), k, "valid"), 1, A)
def lay(o):
    me = o.data; v = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", v); v = v.reshape(-1, 3); M = np.array(o.matrix_world); W = v @ M[:3, :3].T + M[:3, 3]
    c = 2.0; x0, y0 = W[:, 0].min() - 4, W[:, 1].min() - 4; ix, iy = ((W[:, 0] - x0) / c).astype(int), ((W[:, 1] - y0) / c).astype(int)
    nx, ny = ix.max() + 2, iy.max() + 2; low = np.full((nx, ny), np.inf); np.minimum.at(low, (ix, iy), W[:, 2]); low[np.isinf(low)] = np.nan
    sh = np.full((nx, ny), np.nan)
    for i, j in zip(*np.nonzero(~np.isnan(low))):
        s_ = surf(x0 + (i + 0.5) * c, y0 + (j + 0.5) * c)
        if not np.isnan(s_): sh[i, j] = s_ - low[i, j]
    ok = ~np.isnan(sh)
    if not ok.any(): return None
    oi, oj = np.nonzero(ok); vals = sh[ok]                              # fill: each empty cell takes its nearest filled one
    gi, gj = np.mgrid[0:nx, 0:ny]; flat = np.c_[gi.ravel(), gj.ravel()]; filled = sh.copy()
    for start in range(0, len(flat), 20000):
        q = flat[start:start + 20000]; d = (q[:, None, 0] - oi[None]) ** 2 + (q[:, None, 1] - oj[None]) ** 2; nn = d.argmin(1)
        filled.ravel()[start:start + 20000] = vals[nn]
    sm = gauss2(filled, SG / c); W[:, 2] += sm[ix, iy]
    v2 = (W - M[:3, 3]) @ np.linalg.inv(M[:3, :3]).T; me.vertices.foreach_set("co", v2.ravel()); me.update()
    return np.percentile(np.abs(vals), 50), np.abs(vals).max()
hood = bpy.data.objects["piesa_comp_086_tutie"]; hm = hood.data; hv = np.zeros(len(hm.vertices) * 3); hm.vertices.foreach_get("co", hv); hv = hv.reshape(-1, 3)
hv[:, 0] = DX + (hv[:, 0] - DX) * HOOD; hm.vertices.foreach_set("co", hv.ravel()); hm.update()
print("CAPAC 086_tutie ingustat x%.2f: x %.0f..%.0f (fata %s)" % (HOOD, hv[:, 0].min() - DX, hv[:, 0].max() - DX, "neschimbata"))
LP = float(a[4]) if len(a) > 4 else 0.0                   # launch tubes moved to the new hangar pitch
for n, sg in (("launchtube_s_01", -1), ("launchtube_s_03", 1)):
    o = bpy.data.objects.get(n)
    if o and LP:
        me_ = o.data; vv = np.zeros(len(me_.vertices) * 3); me_.vertices.foreach_get("co", vv); vv = vv.reshape(-1, 3); cx_ = (vv[:, 0].min() + vv[:, 0].max()) / 2
        vv[:, 0] += (DX + sg * LP) - cx_; me_.vertices.foreach_set("co", vv.ravel()); me_.update(); print("TUB %s mutat la x %.1f" % (n, sg * LP))
bel = bpy.data.objects["piesa_comp_burta_V"]; mat = bel.data.materials[0] if bel.data.materials else None
Vb = BN["v"].astype(float) + [DX, 0, 0]; me = bpy.data.meshes.new("burta_V_noua"); me.from_pydata(Vb.tolist(), [], [list(f) for f in BN["fq"]] + [list(f) for f in BN["ft"]]); me.validate()
b2 = bmesh.new(); b2.from_mesh(me); bmesh.ops.recalc_face_normals(b2, faces=b2.faces[:]); b2.to_mesh(me); b2.free()
if mat: me.materials.append(mat)
for p in me.polygons: p.use_smooth = True
old = bel.data; bel.data = me; print("BURTA V inlocuita: %d fete (veche %d)" % (len(me.polygons), len(old.polygons)))
for n in ("piesa_comp_055_S", "piesa_comp_055_D", "piesa_comp_103_118_S", "piesa_comp_103_118_D"):
    o = bpy.data.objects.get(n)
    if not o: continue
    r = lay(o); print("ASEZAT %s pe PS nou: mutare mediana %.1f m, max %.1f m" % ((n,) + (r if r else (0, 0))))
    if "103" in n:
        b3 = bmesh.new(); b3.from_mesh(o.data)
        for _ in range(15): bmesh.ops.smooth_vert(b3, verts=b3.verts, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True); bmesh.ops.smooth_vert(b3, verts=b3.verts, factor=-0.53, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        b3.to_mesh(o.data); b3.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
