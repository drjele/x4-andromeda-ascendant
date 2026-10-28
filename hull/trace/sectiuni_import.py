# The volume built from the sections (sectiuni_corp.py) brought into Blender as the new PS body: cut at y = YC, the loops
# taken from the existing new body (its part below YC, the uniform tube), the two open rims of each arm bridged (one ring
# of faces per arm), placed where the exploded new piece is (that one hidden), UVs from the reference (Data Transfer,
# nearest face), its material. Checks: free edges, non-manifold edges, roughness (95 % of neighbour-face angles).
# Usage: blender -b <f.blend> --python sectiuni_import.py -- <corp_sectiuni.npz> <out.blend> [yc]
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; Z = np.load(a[0]); OUT = a[1]; YC = float(a[2]) if len(a) > 2 else -1000.0; XL = 400.0
en, on = bpy.data.objects["expl_piesa_comp_169_C"], bpy.data.objects["piesa_comp_169_C"]; XN = -1700.0 + (en.location.x - on.location.x)
def cut(bm, keep_above):                                               # bisect at y = YC, keep one side, leave the rim open
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, YC, 0), plane_no=(0, 1, 0), clear_inner=keep_above, clear_outer=not keep_above)
new = bmesh.new(); vv = [new.verts.new(tuple(p)) for p in Z["v"]]
for f in Z["f"]:
    try: new.faces.new((vv[f[0]], vv[f[1]], vv[f[2]]))
    except ValueError: pass
bmesh.ops.remove_doubles(new, verts=new.verts, dist=1e-4); bmesh.ops.recalc_face_normals(new, faces=new.faces[:]); cut(new, True)
old = bmesh.new(); old.from_mesh(on.data); old.transform(on.matrix_world); bmesh.ops.translate(old, verts=old.verts, vec=(1700.0, 0, 0))
bmesh.ops.bisect_plane(old, geom=old.verts[:] + old.edges[:] + old.faces[:], plane_co=(0, YC, 0), plane_no=(0, 1, 0))   # the old body: only
gone = [f for f in old.faces if f.calc_center_median().y > YC and abs(f.calc_center_median().x) < XL]   # PS + the arms down to YC go;
bmesh.ops.delete(old, geom=gone, context="FACES")                       # the loops' outer branches (far out) stay whole
me = bpy.data.meshes.new("piesa_169_C_sectiuni"); new.to_mesh(me); tmp = bpy.data.meshes.new("t"); old.to_mesh(tmp)
bm = bmesh.new(); bm.from_mesh(me); bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
rims = [e for e in bm.edges if e.is_boundary and abs(e.verts[0].co.y - YC) < 0.5 and abs(e.verts[1].co.y - YC) < 0.5 and abs(e.verts[0].co.x) < XL]
for sg in (1, -1):                                                     # the two rims of each arm compared (before the bridge)
    for lab, src_ in (("nou", "n"), ("vechi", "o")):
        pass
import collections
def loops_of(es):
    adj = collections.defaultdict(list)
    for e in es:
        for v in e.verts: adj[v].append(e)
    seen, out = set(), []
    for e in es:
        if e in seen: continue
        st, comp = [e], []; seen.add(e)
        while st:
            x = st.pop(); comp.append(x)
            for v in x.verts:
                for f_ in adj[v]:
                    if f_ not in seen: seen.add(f_); st.append(f_)
        out.append(comp)
    return out
for c_ in loops_of(rims):
    P_ = np.array([tuple(v.co) for e in c_ for v in e.verts]); print("MARGINE la y %.0f: %d muchii, centru (%.1f, %.1f), lat %.1f, inalt %.1f" % (YC, len(c_), P_[:, 0].mean(), P_[:, 2].mean(), np.ptp(P_[:, 0]), np.ptp(P_[:, 2])))
for sg in (1, -1):                                                     # per arm: its two rims (new above, old below) bridged
    es = [e for e in rims if e.verts[0].co.x * sg > 0]
    if es: bmesh.ops.bridge_loops(bm, edges=es)
band = [v for v in bm.verts if abs(v.co.y - YC) < 40]                   # the stitch: neighbour averages over a 40 m band, eased
for it in range(30):
    P = {v: v.co.copy() for v in band}
    for v in band:
        nb = [e.other_vert(v).co for e in v.link_edges]
        if nb: w_ = 0.5 * (1 - abs(v.co.y - YC) / 40); v.co = P[v] * (1 - w_) + sum(nb, P[v] * 0) / len(nb) * w_
bm.normal_update(); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
fb = sum(1 for e in bm.edges if e.is_boundary); nm = sum(1 for e in bm.edges if len(e.link_faces) > 2)
ang = np.degrees([e.calc_face_angle(0) for e in bm.edges if len(e.link_faces) == 2])
bm.to_mesh(me); bm.free(); new.free(); old.free()
o = bpy.data.objects.new("piesa_169_C_sectiuni", me); o.location.x = XN
col = bpy.data.collections.get("PS_SECTIUNI") or bpy.data.collections.new("PS_SECTIUNI")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for x in list(col.objects): bpy.data.objects.remove(x)
col.objects.link(o)
for p in me.polygons: p.use_smooth = True
me.materials.append(en.material_slots[0].material if en.material_slots else None)
src = bpy.data.objects["expl_R002 169_C"]; c = src.copy(); c.data = src.data.copy(); bpy.context.scene.collection.objects.link(c)
c.data.transform(src.matrix_world); c.matrix_world.identity()           # the reference moved onto the new body (middles matched)
c.location.x = XN - (-4.68 + (src.location.x - bpy.data.objects["R002 169_C"].location.x))
me.uv_layers.new(name="UVMap"); md = o.modifiers.new("uv", "DATA_TRANSFER"); md.object = c; md.use_object_transform = True
md.use_loop_data = True; md.data_types_loops = {"UV"}; md.loop_mapping = "POLYINTERP_NEAREST"
bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=md.name); bpy.data.objects.remove(c)
en.hide_set(True); en.hide_render = True
print("CORP SECTIUNI: %d varfuri, %d fete; muchii libere %d (capetele tubului), nemanifold %d; asperitate 95%% %.1f grade, max %.0f" % (
    len(me.vertices), len(me.polygons), fb, nm, np.percentile(ang, 95), ang.max()))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
