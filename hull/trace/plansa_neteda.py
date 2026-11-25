# Board block NAVA_NETEDA: the smooth components (neteda.npz, S half + exact mirror, one object per component, the confirmed colours)
# and linked copies of the confirmed pieces of ASAMBLAT_NOU coloured by component (PS, BF; BS is its own rows). Colours sit on the object,
# the confirmed meshes and materials stay untouched. Usage: blender -b <scene> --python plansa_neteda.py -- <npz> <x> <out.blend> [<collection> <prefix>]
import bpy, sys, os, numpy as np
AR = sys.argv[sys.argv.index("--") + 1:]; NPZ, X, OUT = AR[:3]; X = float(X); COL, PRE = (AR[3:] + ["NAVA_NETEDA", "net_"])[:2] if len(AR) > 4 else ("NAVA_NETEDA", "net_"); assert not os.path.exists(OUT)
COLS = {"PS": (.85, .85, .85), "BF": (.95, .75, .1), "BS": (.45, .28, .12), "BJ": (.1, .25, .9), "PI (ARCU)": (.15, .7, .15), "CORP": (.8, .08, .08), "CORP etaj": (1, .42, .05), "AI": (.05, .65, .7), "AS": (.95, .35, .65), "H": (.45, .1, .75)}
c = bpy.data.collections.new(COL); bpy.context.scene.collection.children.link(c); z = np.load(NPZ)
def mat(q):
    n = "comp_" + q; m = bpy.data.materials.get(n) or bpy.data.materials.new(n); m.diffuse_color = (*COLS[q], 1); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value = (*COLS[q], 1); p.inputs["Roughness"].default_value = .55; return m
for q in ("BS", "BJ", "PI (ARCU)", "CORP", "CORP etaj", "AI", "AS", "H"):
    v, f = z["v__" + q].astype(float), z["f__" + q]; k = len(v); on = np.abs(v[:, 0]) < 1e-4; idx = np.arange(k, 2 * k); cnt = np.cumsum(~on) - 1; idx = np.where(on, np.arange(k), k + cnt); V = np.vstack([v, v[~on] * [-1, 1, 1]]); F = np.vstack([f, idx[f][:, ::-1]])
    n = PRE + q.replace(" (ARCU)", "").replace(" ", "_"); me = bpy.data.meshes.new(n); me.from_pydata(V.tolist(), [], F.tolist()); me.materials.append(mat(q)); me.polygons.foreach_set("use_smooth", [True] * len(me.polygons)); me.update(); 
    if "n__" + q in z: w = z["n__" + q].astype(float); w[on, 0] = 0; me.normals_split_custom_set_from_vertices(np.vstack([w, w[~on] * [-1, 1, 1]]).tolist())   # the surface's own normals
    else: import bmesh; bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(n, me); o.location.x = X; c.objects.link(o); o.color = (*COLS[q], 1)
new = "cut_p" in z                                                          # from nava_neteda4 on: arm tips replaced, blades animated, drawn out
if new:
    root = bpy.data.objects.new(PRE + "animatie", None); root.location.x = X + 2400; c.objects.link(root); import bmesh; from mathutils import Vector
    bpy.context.scene.frame_set(1)
for o in list(bpy.data.collections["ASAMBLAT_NOU"].all_objects):
    if o.name.startswith("an_brat_spate") or (new and o.name.startswith("an_lacrima_brat")): continue
    q = "BF" if any(s in o.name for s in ("brat_fata", "nacela", "lama", "usa_fata", "usa_spate", "lacrima_brat", "spinare", "R060")) else "PS"
    d = o.copy(); d.name = PRE + o.name
    if new: c.objects.link(d); d.parent = root; d.matrix_parent_inverse.identity()
    else: d.animation_data_clear(); d.matrix_world = o.matrix_world.copy(); d.parent = None; d.location.x += X + 2400; c.objects.link(d)
    if new and o.name.startswith("an_brat_fata"):                           # own mesh, cut where the new tip starts
        d.data = o.data.copy(); sg = -1 if o.name.endswith("_D") else 1; cp = Vector(z["cut_p"]) * 1; cp.x *= sg; ct = Vector(z["cut_t"]); ct.x *= sg; M = o.matrix_world.inverted(); bm = bmesh.new(); bm.from_mesh(d.data)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=M @ (cp + Vector((-2400, 0, 0))), plane_no=(M.to_3x3() @ ct).normalized(), clear_outer=True); bm.to_mesh(d.data); bm.free()
    if new and ("lama" in o.name or "spinare" in o.name): d.color = (.55, .02, .03, 1); continue      # blades keep their own red and black edge
    for i in range(len(d.material_slots)): d.material_slots[i].link = "OBJECT"; d.material_slots[i].material = mat(q)
    d.color = (*COLS[q], 1)
if new:
    v, f, w = z["v__BF varf"].astype(float), z["f__BF varf"], z["n__BF varf"].astype(float); k = len(v); n = PRE + "brat_fata_varf"; me = bpy.data.meshes.new(n); me.from_pydata(np.vstack([v, v * [-1, 1, 1]]).tolist(), [], np.vstack([f, f[:, ::-1] + k]).tolist()); me.materials.append(mat("BF")); me.polygons.foreach_set("use_smooth", [True] * len(me.polygons)); me.update(); me.normals_split_custom_set_from_vertices(np.vstack([w, w * [-1, 1, 1]]).tolist()); o = bpy.data.objects.new(n, me); o.location.x = X; o.color = (*COLS["BF"], 1); c.objects.link(o); bpy.context.scene.frame_set(100)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("PLANSA", len(c.objects))
