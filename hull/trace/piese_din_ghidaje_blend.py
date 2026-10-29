# The pieces from piese_din_ghidaje.py into the scene, twice: assembled (location x XA) and exploded (x XE + each piece's
# explode offset); open boundaries filled (flat caps), normals outwards, triangulated; materials from the matching pieces
# already in the scene; new collections, nothing existing touched. Chambers in the npz cut the hood (hollow); ears = pieces.
# Usage: blender -b <in> --python piese_din_ghidaje_blend.py -- <out.blend> <piese npz> <XA> <XE>
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, P, XA, XE = a[0], np.load(a[1]), float(a[2]), float(a[3])
SRC = {"PS": "sep_PS", "PS_rama": "sep_PS_rama", "PS_carena": "sep_PS_carena", "capac_086": "sep_capac_086", "brat_spate_D": "sep_brat_spate_D", "brat_spate_S": "sep_brat_spate_S"}
EXP = {"PS": (0, 0, 0), "PS_rama": (0, 0, -45), "PS_carena": (0, 0, -110), "capac_086": (0, 0, 90), "brat_spate_D": (80, -120, 0), "brat_spate_S": (-80, -120, 0)}
def mesh(name):
    v = P[name + "__v"]; f = P[name + "__f"]; bm = bmesh.new(); vs = [bm.verts.new(p) for p in v]; bm.verts.ensure_lookup_table()
    for t in f:
        try: bm.faces.new([vs[i] for i in t])
        except ValueError: pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bd = [e for e in bm.edges if e.is_boundary]
    if bd: bmesh.ops.holes_fill(bm, edges=bd, sides=0)
    bmesh.ops.triangulate(bm, faces=[q for q in bm.faces if len(q.verts) > 3]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    nb = sum(1 for e in bm.edges if not e.is_manifold); me = bpy.data.meshes.new("g_" + name); bm.to_mesh(me); bm.free(); return me, nb
for nm_ in [k[:-3] for k in P.files if k.startswith("urechiusa_") and k.endswith("__v")]:     # the little ears, like the keel
    SRC[nm_] = "sep_PS_carena"; EXP[nm_] = (70 if nm_.endswith("_D") else -70, 0, -75)
def boolean_diff(o, me_cut):
    c = bpy.data.objects.new("tmp_cut", me_cut); bpy.context.scene.collection.objects.link(c); c.location = o.location.copy()   # same frame as the hood
    m = o.modifiers.new("b", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = c; m.solver = "EXACT"
    bpy.context.view_layer.objects.active = o
    for ob in bpy.context.view_layer.objects: ob.select_set(ob == o)
    bpy.ops.object.modifier_apply(modifier="b"); bpy.data.objects.remove(c)
for tag, X, exp in (("ASAMBLAT", XA, False), ("EXPLODAT", XE, True)):
    col = bpy.data.collections.new("PIESE_DIN_GHIDAJE_" + tag); bpy.context.scene.collection.children.link(col)
    for name in SRC:
        me, nb = mesh(name)
        src = bpy.data.objects.get(SRC[name]) or bpy.data.objects.get("gp_" + name)   # the old sep_ set may be gone: the pieces' own materials
        if src:
            for m in src.data.materials: me.materials.append(m)
        o = bpy.data.objects.new(("gp_" if not exp else "gpe_") + name, me); col.objects.link(o)
        d = EXP[name] if exp else (0, 0, 0); o.location = (X + d[0], d[1], d[2])
        if name == "capac_086" and "camera_D__v" in P.files:                    # hollow: the two chambers taken out
            for sd in ("D", "S"): mc, _ = mesh("camera_" + sd); boolean_diff(o, mc)
        if tag == "ASAMBLAT": print("PIESA %-14s %7d fete, muchii ne-manifold %d" % (name, len(o.data.polygons), nb))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
