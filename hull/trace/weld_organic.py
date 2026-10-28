# The body of each variant welded into one closed organic surface: its pieces joined and rebuilt as a volume (voxel
# remesh, VOXEL m), so pieces that meet merge with a continuous joint; then smoothed lightly (SMOOTH_ITERS passes) so
# the joints become rounded fillets; then made exactly symmetric (the user's absolute rule): cut on the centre plane,
# the left half kept and mirrored with the seam merged. The blades stay separate parts (they fold) and are made
# symmetric too (each cut on the centre plane, its left half mirrored). The welded body takes the original's normals
# (data transfer), so it shades as smoothly as the original even where the source surface is coarse. The original pieces are kept hidden in a collection for comparison.
# Usage: blender -b <variants.blend> --python weld_organic.py -- <out.blend> <voxel_m> <smooth_iters> <factor> <prefix:corp_coll:lame_coll> ...
import bpy, bmesh, sys
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; OUT, VOXEL, ITERS = a[0], float(a[1]), int(a[2]); LAMBDA = float(a[3]); SPECS = [s.split(":") for s in a[4:]]
sc = bpy.context.scene
def objs(name): c = bpy.data.collections.get(name); return [o for o in c.objects if o.type == "MESH"] if c else []
def centre_x(obs): xs = [(o.matrix_world @ Vector(b)).x for o in obs for b in o.bound_box]; return (min(xs) + max(xs)) / 2
def select(obs, active):
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = active
def symmetrize(o, cx):
    # exact mirror about x = cx: the left half kept, mirrored, the seam welded
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(cx, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
    for v in bm.verts:
        if abs(v.co.x - cx) < 1e-4: v.co.x = cx
    m = bmesh.new(); m.from_mesh(o.data)
    geom = bmesh.ops.duplicate(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:])["geom"]
    for v in [g for g in geom if isinstance(g, bmesh.types.BMVert)]: v.co.x = 2 * cx - v.co.x
    bmesh.ops.reverse_faces(bm, faces=[g for g in geom if isinstance(g, bmesh.types.BMFace)])
    bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if abs(v.co.x - cx) < 1e-3], dist=1e-3)
    o.matrix_world = Matrix.Identity(4); bm.to_mesh(o.data); bm.free(); m.free()
def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)
keep = bpy.data.collections.new("ORIGINAL_piese_ascunse"); sc.collection.children.link(keep)
for pre, corp, lame in SPECS:
    body = objs(corp); cx = centre_x(body)
    # copies of the pieces kept for comparison, hidden
    ref = []
    for o in body:
        c = o.copy(); c.data = o.data.copy(); keep.objects.link(c); c.hide_set(True); c.hide_render = True; ref.append(c)
    select(body, body[0]); bpy.ops.object.join(); b = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    n0 = tris(b); b.data.remesh_voxel_size = VOXEL; b.data.remesh_voxel_adaptivity = 0.0; bpy.ops.object.voxel_remesh()
    if ITERS:                                                             # plain smoothing (fast, threaded): rounds facets and joints
        md = b.modifiers.new("organic", "SMOOTH"); md.factor = LAMBDA; md.iterations = ITERS; bpy.ops.object.modifier_apply(modifier=md.name)
    symmetrize(b, cx); b.name = pre + "_corp_sudat"; bpy.ops.object.shade_smooth()
    # the original's shading carried onto the welded surface: its interpolated normals (what makes the coarse source look
    # smooth) transferred from the nearest original faces, so the welded ship shades exactly like the original
    src = [c.copy() for c in ref]
    for c in src: c.data = c.data.copy(); keep.objects.link(c)
    select(src, src[0]); bpy.ops.object.join(); srcj = bpy.context.view_layer.objects.active; srcj.name = pre + "_sursa_normale"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); bpy.ops.object.shade_smooth(); srcj.hide_render = True
    select([b], b); md = b.modifiers.new("normale_originale", "DATA_TRANSFER"); md.object = srcj; md.use_loop_data = True
    md.data_types_loops = {"CUSTOM_NORMAL"}; md.loop_mapping = "POLYINTERP_NEAREST"
    try: bpy.ops.object.modifier_apply(modifier=md.name)
    except Exception as e: print("transfer normale:", e)
    srcj.hide_set(True)
    # a transferred normal facing against the welded face (taken from an inner, inward-facing original surface) is turned
    # back; one more than 60 deg off the face is replaced by the face's own normal (no dark patches)
    import numpy as np
    me = b.data; nl = len(me.loops); cn = np.zeros(nl * 3); me.corner_normals.foreach_get("vector", cn); cn = cn.reshape(-1, 3)
    pn = np.zeros(len(me.polygons) * 3); me.polygons.foreach_get("normal", pn); pn = pn.reshape(-1, 3)
    li = np.zeros(nl, int); 
    for p_ in me.polygons: li[p_.loop_start:p_.loop_start + p_.loop_total] = p_.index
    f = pn[li]; d = (cn * f).sum(1); cn[d < 0] *= -1; d = np.abs(d); bad = d < 0.5; cn[bad] = f[bad]
    me.normals_split_custom_set(cn.tolist()); print(pre, "normale: %d intoarse, %d inlocuite cu normala fetei din %d" % (int((d < 0).sum()), int(bad.sum()), nl))
    print(pre, "corp: %d piese -> 1 suprafata, %d -> %d triunghiuri (voxel %.2f m, netezire %d), axa x=%.2f" % (len(body), n0, tris(b), VOXEL, ITERS, cx))
    # blades: each one cut on the centre plane and mirrored like the body (an object may hold blades of both sides)
    bl = objs(lame); n_empty = 0
    for o in bl:
        symmetrize(o, cx)
        if not o.data.polygons: bpy.data.objects.remove(o); n_empty += 1
    print(pre, "lame: %d obiecte simetrizate (%d goale scoase)" % (len(bl) - n_empty, n_empty))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
