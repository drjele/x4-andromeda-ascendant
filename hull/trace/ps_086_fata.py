# The hood's front closed (asked: no gaps on the front except the hangars): one front wall across the room's opening,
# from one inner side wall to the other and from the floor up into the lid, following the lid's front curve, THICK deep,
# with NTUB door openings exactly the launch tubes' doors (40 x 30 m at the Colossus pitch); it replaces the comb teeth.
# Built on a 1 m grid in the front plane (cells inside a door left out), then given its depth. Ship coordinates.
# Usage: blender -b <file.blend> --python ps_086_fata.py -- <esantion_punte.npz> <out.blend> <dx> [name]
import bpy, bmesh, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; S = np.load(a[0]); OUT, DX = a[1], float(a[2]); NAME = a[3] if len(a) > 3 else "piesa_comp_086_fata"
env = lambda k, d: float(os.environ.get(k, d))
WT, ZF, ZC, TP, DEP = env("P086_PERETE_GROS", "4"), env("P086_PODEA", "316"), env("P086_CAPAC_Z", "354"), env("P086_GROSIME", "3"), env("P086_FATA_GROS", "4")
NTUB, PAS, TW_, TH_ = int(env("P086_TUBURI", "3")), env("P086_TUB_PAS", "51.5"), 40.0, 30.0
q = S["p086"]; YB, YF = q[:, 1].min(), q[:, 1].max(); xc_ = (q[:, 0].min() + q[:, 0].max()) / 2
yy = np.arange(YB, YF, 4.0); hw = np.array([(abs(q[np.abs(q[:, 1] - y) < 2][:, 0].min()) + q[np.abs(q[:, 1] - y) < 2][:, 0].max()) / 2 for y in yy])
A_ = np.polyfit(yy[yy < YF - 40], hw[yy < YF - 40], 1); WF = float(np.polyval(A_, YF))
if os.environ.get("P086_FATA_W"): WF = float(os.environ["P086_FATA_W"])   # a narrower front (hangars closer together)
fx = np.arange(-WF + 4, WF - 4, 4.0); fy = np.array([q[np.abs(q[:, 0] - xc_ - x) < 2][:, 1].max() for x in fx])
cF = float(np.linalg.lstsq((fx ** 2)[:, None], YF - fy, rcond=None)[0][0]); front = lambda x: YF - cF * x ** 2
XW = WF - WT + 0.5; tc = (np.arange(NTUB) - (NTUB - 1) / 2) * PAS; z0, z1 = ZF - 1.0, ZC - TP + 0.5   # into the walls, floor and lid
xs = np.r_[np.arange(-XW, XW, 1.0), XW]; zs = np.r_[np.arange(z0, z1, 1.0), z1]
def door(x, z): return any(abs(x - c) < TW_ / 2 for c in tc) and ZF + 1.0 < z < ZF + 1.0 + TH_
bm = bmesh.new(); vg = {}
def vert(i, j):
    if (i, j) not in vg: vg[(i, j)] = bm.verts.new((xs[i] + DX, front(xs[i]) - 0.5, zs[j]))
    return vg[(i, j)]
xs = np.unique(np.r_[xs, [c + d for c in tc for d in (-TW_ / 2, TW_ / 2)]]); zs = np.unique(np.r_[zs, ZF + 1.0, ZF + 1.0 + TH_])   # door edges on the grid
for i in range(len(xs) - 1):
    for j in range(len(zs) - 1):
        if door((xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2): continue
        bm.faces.new((vert(i, j), vert(i + 1, j), vert(i + 1, j + 1), vert(i, j + 1)))
r = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:]); nv = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
for v in nv: v.co.y -= DEP                                             # depth: back into the room
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bnd = sum(1 for e in bm.edges if e.is_boundary); nm_ = sum(1 for e in bm.edges if len(e.link_faces) > 2)
if NAME in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[NAME])
me = bpy.data.meshes.new(NAME); bm.to_mesh(me); bm.free()
src = bpy.data.objects["R082 086_S"]; me.materials.append(src.material_slots[src.data.polygons[0].material_index].material)
col = bpy.data.collections.get(os.environ.get("COLECTIE", "PS_PIESE")) or bpy.data.collections.new(os.environ.get("COLECTIE", "PS_PIESE"))
o = bpy.data.objects.new(NAME, me); col.objects.link(o)
for old in ("piesa_comp_086_dinti",):
    oo = bpy.data.objects.get(old)
    if oo:
        oo.hide_render = True
        try: oo.hide_set(True)
        except RuntimeError: pass
print("086 FATA: perete frontal %.0f x %.0f m, %.0f m adanc, %d usi de %.0f x %.0f m la x %s; muchii libere %d, nemanifold %d" % (2 * XW, z1 - z0, DEP, NTUB, TW_, TH_, np.round(tc, 1).tolist(), bnd, nm_))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
