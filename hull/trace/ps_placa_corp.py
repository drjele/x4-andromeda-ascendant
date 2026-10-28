# A plate component laid on the PS body from its outline seen from above (ps_contur_sus.py): the outline filled,
# subdivided to <= 2 m edges; bottom just inside the body's top surface (EMBED below it), top THICK above the surface;
# the rim joins them. Built for _S from the outline, _D its mirror. Ship coordinates (x + DX), moved by OFF.
# Usage: blender -b <file.blend> --python ps_placa_corp.py -- <contur.npz> <corp.npz> <out.blend> <dx> <name> <material_from> [off]
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; L = np.load(a[0])["loop"]; B = np.load(a[1]); OUT, DX, NAME, MSRC = a[2], float(a[3]), a[4], a[5]
OFF = Vector([float(v) for v in a[6].split(",")]) if len(a) > 6 else Vector()
TH, EMB = float(os.environ.get("PLACA_GROSIME", "2")), float(os.environ.get("PLACA_INFIPT", "0.5"))
ys, s_, E, T = B["ys"], B["s"], B["edge"], B["top"]
def zb(x, y):
    k = int(np.clip(np.searchsorted(ys, y), 1, len(ys) - 1)); f = (y - ys[k - 1]) / (ys[k] - ys[k - 1])
    return (1 - f) * np.interp(abs(x), s_ * E[k - 1], T[k - 1]) + f * np.interp(abs(x), s_ * E[k], T[k])
col = bpy.data.collections.get(os.environ.get("COLECTIE", "PS_PIESE")) or bpy.data.collections.new(os.environ.get("COLECTIE", "PS_PIESE"))
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
src = bpy.data.objects[MSRC]; mat = src.material_slots[src.data.polygons[0].material_index].material
for side, sg in (("S", 1), ("D", -1)):
    bm = bmesh.new(); vs = [bm.verts.new((sg * x, y, 0)) for x, y in (L if sg > 0 else L[::-1])]; bm.faces.new(vs); bmesh.ops.triangulate(bm, faces=bm.faces[:])
    for _ in range(10):
        long_ = [e for e in bm.edges if e.calc_length() > 2.0]
        if not long_: break
        bmesh.ops.subdivide_edges(bm, edges=long_, cuts=1, use_grid_fill=False); bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.beautify_fill(bm, faces=bm.faces[:], edges=bm.edges[:])
    for v in bm.verts: v.co.z = zb(v.co.x, v.co.y) - EMB
    dup = bmesh.ops.duplicate(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:])
    for v in [g for g in dup["geom"] if isinstance(g, bmesh.types.BMVert)]: v.co.z += EMB + TH
    bmesh.ops.bridge_loops(bm, edges=[e for e in bm.edges if e.is_boundary]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for v in bm.verts: v.co.x += DX
    nm = "%s_%s" % (NAME, side)
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm])
    me = bpy.data.meshes.new(nm); bm.to_mesh(me); bnd = sum(1 for e in bm.edges if e.is_boundary); bm.free(); me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(nm, me); col.objects.link(o); o.location = OFF
    print("PLACA %s: %d varfuri, %d fete, muchii libere %d" % (nm, len(me.vertices), len(me.polygons), bnd))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
