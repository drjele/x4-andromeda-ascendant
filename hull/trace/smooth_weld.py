# The body of each variant welded and smoothed on its OWN surface (textures/UVs kept, no rebuild): the pieces joined
# into one object, vertices that coincide where pieces meet merged (WELD m) so the pieces are one surface there; long
# edges of coarse faces split (MAX_EDGE m) so big flat facets can bend; Taubin smoothing (a shrink then an inflate step,
# so shape and volume stay, as in smooth_all.py) for PASSES passes, with open borders and the vertices on sharp edges
# (dihedral above SHARP_DEG) pinned, so what is sharp stays sharp; then made exactly symmetric (the user's absolute
# rule): cut on the centre plane, the left half mirrored, the seam merged; the original's stored smooth normals then
# transferred (the coarse source looks smooth through them). Blades stay separate parts (they fold),
# smoothed the same way and made symmetric. Hidden copies of the original pieces kept for comparison.
# Usage: blender -b <variants.blend> --python smooth_weld.py -- <out.blend> <passes> <prefix:corp_coll:lame_coll> ...
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; OUT, PASSES = a[0], int(a[1]); SPECS = [s.split(":") for s in a[2:]]
WELD, MAX_EDGE, SHARP_DEG, LAM, MU = 0.2, 6.0, 40.0, 0.5, -0.53
sc = bpy.context.scene
def objs(name): c = bpy.data.collections.get(name); return [o for o in c.objects if o.type == "MESH"] if c else []
def centre_x(obs): xs = [(o.matrix_world @ Vector(b)).x for o in obs for b in o.bound_box]; return (min(xs) + max(xs)) / 2
def select(obs, active):
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = active
def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)
def weld_split(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=WELD)
    for _ in range(4):                                                    # long edges split until none is longer than MAX_EDGE
        long_ = [e for e in bm.edges if e.calc_length() > MAX_EDGE]
        if not long_: break
        bmesh.ops.subdivide_edges(bm, edges=long_, cuts=1, use_grid_fill=False)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.to_mesh(o.data); bm.free()
def taubin(o, passes):
    me = o.data; bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    v = np.array([x.co[:] for x in bm.verts]); e = np.array([[x.verts[0].index, x.verts[1].index] for x in bm.edges])
    pin = np.zeros(len(v), bool)
    for ed in bm.edges:
        if ed.is_boundary or not ed.is_manifold or (len(ed.link_faces) == 2 and ed.calc_face_angle(0) > math.radians(SHARP_DEG)):
            pin[ed.verts[0].index] = pin[ed.verts[1].index] = True
            if not ed.is_boundary: ed.smooth = False                     # sharp edges shaded sharp
    deg = np.bincount(e.ravel(), minlength=len(v)).astype(float); free = (deg > 0) & ~pin
    def lap(x):
        s = np.zeros_like(x); np.add.at(s, e[:, 0], x[e[:, 1]]); np.add.at(s, e[:, 1], x[e[:, 0]]); return s / np.maximum(deg, 1)[:, None] - x
    for _ in range(passes):
        for f in (LAM, MU): v[free] += f * lap(v)[free]
    for i, bv in enumerate(bm.verts): bv.co = v[i]
    for f in bm.faces: f.smooth = True
    bm.to_mesh(me); bm.free(); return int(free.sum()), int(pin.sum())
def symmetrize(o, cx):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(cx, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
    for v in bm.verts:
        if abs(v.co.x - cx) < 1e-4: v.co.x = cx
    geom = bmesh.ops.duplicate(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:])["geom"]
    for v in [g for g in geom if isinstance(g, bmesh.types.BMVert)]: v.co.x = 2 * cx - v.co.x
    bmesh.ops.reverse_faces(bm, faces=[g for g in geom if isinstance(g, bmesh.types.BMFace)])
    bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if abs(v.co.x - cx) < 1e-3], dist=1e-3)
    o.matrix_world = Matrix.Identity(4); bm.to_mesh(o.data); bm.free()
def transfer_normals(b, ref, pre):
    # the original's smooth shading (its stored normals) carried onto the welded, smoothed surface: nearest-face normals,
    # one facing against the face turned back, one more than 60 deg off replaced by the face's own normal
    src = [c.copy() for c in ref]; col = bpy.data.collections["ORIGINAL_piese_ascunse"]
    for c in src: c.data = c.data.copy(); col.objects.link(c)
    select(src, src[0]); bpy.ops.object.join(); sj = bpy.context.view_layer.objects.active; sj.name = pre + "_sursa_normale"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); sj.hide_render = True
    select([b], b); md = b.modifiers.new("normale_originale", "DATA_TRANSFER"); md.object = sj; md.use_loop_data = True
    md.data_types_loops = {"CUSTOM_NORMAL"}; md.loop_mapping = "POLYINTERP_NEAREST"; bpy.ops.object.modifier_apply(modifier=md.name); sj.hide_set(True)
    me = b.data; nl = len(me.loops); cn = np.zeros(nl * 3); me.corner_normals.foreach_get("vector", cn); cn = cn.reshape(-1, 3)
    pn = np.zeros(len(me.polygons) * 3); me.polygons.foreach_get("normal", pn); pn = pn.reshape(-1, 3)
    ls = np.zeros(len(me.polygons), int); lt = np.zeros(len(me.polygons), int); me.polygons.foreach_get("loop_start", ls); me.polygons.foreach_get("loop_total", lt)
    f = pn[np.repeat(np.arange(len(ls)), lt)]; d = (cn * f).sum(1); cn[d < 0] *= -1; bad = np.abs(d) < 0.5; cn[bad] = f[bad]
    me.normals_split_custom_set(cn.tolist()); print(pre, "normale transferate; %d inlocuite cu normala fetei din %d" % (int(bad.sum()), nl))
keep = bpy.data.collections.new("ORIGINAL_piese_ascunse"); sc.collection.children.link(keep)
for pre, corp, lame in SPECS:
    body = objs(corp); cx = centre_x(body)
    ref = []
    for o in body:
        c = o.copy(); c.data = o.data.copy(); keep.objects.link(c); c.hide_set(True); c.hide_render = True; ref.append(c)
    select(body, body[0]); bpy.ops.object.join(); b = bpy.context.view_layer.objects.active; b.name = pre + "_corp_sudat_netezit"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); n0 = tris(b)
    weld_split(b); fr, pn = taubin(b, PASSES); symmetrize(b, cx); transfer_normals(b, ref, pre)
    print(pre, "corp: %d piese -> 1, %d -> %d triunghiuri, Taubin %d treceri (%d varfuri mobile, %d fixe pe muchii ascutite/borduri)" % (len(body), n0, tris(b), PASSES, fr, pn))
    for o in objs(lame):
        select([o], o); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); taubin(o, max(PASSES // 3, 1)); symmetrize(o, cx)
    print(pre, "lame: netezite + simetrizate")
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
