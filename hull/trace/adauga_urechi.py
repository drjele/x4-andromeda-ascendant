# The big ears (ureche_D / ureche_S from ureche_din_vertebre.py) put with the PS's pieces: into the fit area (pot_, x XP),
# the assembled block (gp_, x XA) and the exploded one (gpe_, x XE, moved EX m outwards); flat end caps, normals out,
# the PS's materials; old ones of the same name replaced. Separate objects (never fused).
# Usage: blender -b <in> --python adauga_urechi.py -- <out.blend> <ureche npz> [XP=-15000 XA=-9400 XE=-11200 EX=90]
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, P = a[0], np.load(a[1])
XP, XA, XE, EX = (float(v) for v in (a[2:6] if len(a) >= 6 else (-15000, -9400, -11200, 90)))
def mesh(name, sd):
    v = P["ureche_%s__v" % sd]; f = P["ureche_%s__f" % sd]; bm = bmesh.new(); vs = [bm.verts.new(p) for p in v]; bm.verts.ensure_lookup_table()
    for t in f:
        try: bm.faces.new([vs[i] for i in t])
        except ValueError: pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-3); bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges)
    bd = [e for e in bm.edges if e.is_boundary]
    if bd: bmesh.ops.holes_fill(bm, edges=bd, sides=0)
    bmesh.ops.triangulate(bm, faces=[q for q in bm.faces if len(q.verts) > 3]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    nm = sum(1 for e in bm.edges if not e.is_manifold); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in bpy.data.objects["gp_PS"].data.materials: me.materials.append(m)
    return me, nm
for pre, col, x0, ex in (("pot_", "URECHE_POTRIVIRE", XP, 0), ("gp_", "PIESE_DIN_GHIDAJE_ASAMBLAT", XA, 0), ("gpe_", "PIESE_DIN_GHIDAJE_EXPLODAT", XE, EX)):
    for sd, sg in (("D", 1), ("S", -1)):
        if col not in bpy.data.collections: continue                   # a block not on this board
        n = pre + "ureche_" + sd; o0 = bpy.data.objects.get(n)
        if o0: bpy.data.objects.remove(o0)
        me, nm = mesh(n, sd); o = bpy.data.objects.new(n, me); bpy.data.collections[col].objects.link(o); o.location.x = x0 + sg * ex
        print("URECHE %-14s %6d fete, ne-manifold %d, x %.0f" % (n, len(me.polygons), nm, o.location.x))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
