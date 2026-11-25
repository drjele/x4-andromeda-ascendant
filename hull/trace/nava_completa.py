# The whole ship as separate pieces: the closed smooth pieces (solide.npz, S half + exact mirror, one object per side) and the confirmed
# pieces of ASAMBLAT_NOU with their animation. The front arms get their own mesh: faces turned outwards, the one opening of the confirmed
# arm (door tunnel through the top skin) closed with the intact skin, cut where the new tip starts. The board keeps only the blocks
# named in KEEP. Usage: blender -b <scene> --python nava_completa.py -- <solide.npz> <intact skin npz> <x> <out.blend> <KEEP ...>
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
NPZ, SKIN, X, OUT, *KEEP = sys.argv[sys.argv.index("--") + 1:]; X = float(X); assert not os.path.exists(OUT); z = np.load(NPZ); sc = bpy.context.scene; sc.frame_set(1)
COLS = {"PS": (.85, .85, .85), "BF": (.95, .75, .1), "BS": (.45, .28, .12), "BJ": (.1, .25, .9), "PI (ARCU)": (.15, .7, .15), "CORP": (.8, .08, .08), "CORP etaj": (1, .42, .05), "AI": (.05, .65, .7), "AS": (.95, .35, .65), "H": (.45, .1, .75)}
NAME = {"PI (ARCU)": "PI", "CORP etaj": "CORP_etaj", "BF varf": "brat_fata_varf"}; CENTRAL = ("CORP", "CORP etaj", "PI (ARCU)")
c = bpy.data.collections.new("NAVA_COMPLETA"); sc.collection.children.link(c); root = bpy.data.objects.new("nava", None); root.location.x = X; c.objects.link(root)
def mat(q):
    n = "comp_" + q; m = bpy.data.materials.get(n) or bpy.data.materials.new(n); m.diffuse_color = (*COLS[q], 1); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*COLS[q], 1); return m
def put(n, v, t, nr, skin, q):
    me = bpy.data.meshes.new(n); me.from_pydata(v.tolist(), [], t.tolist()); me.materials.append(mat(q)); me.polygons.foreach_set("use_smooth", skin.tolist()); me.update(); fn = np.empty(len(t) * 3); me.polygons.foreach_get("normal", fn); fn = fn.reshape(-1, 3); ln = nr[t]; bad = np.linalg.norm(ln, axis=2) < .5
    ln[bad] = np.repeat(fn[:, None], 3, 1)[bad]; ln[~skin] = fn[~skin][:, None]; me.normals_split_custom_set(ln.reshape(-1, 3).tolist()); o = bpy.data.objects.new(n, me); o.parent = root; o.color = (*COLS[q], 1); c.objects.link(o); return o
for k in z["names"]:
    k = str(k); v, t, nr, sk = z[k + "|v"].copy(), z[k + "|t"], z[k + "|n"].copy(), z[k + "|s"]; n = "nava_" + NAME.get(k, k); q = "BF" if k == "BF varf" else k; mv, mn = v * [-1, 1, 1], nr * [-1, 1, 1]
    if k in CENTRAL: put(n, v, t, nr, sk, q)
    else: put(n + "_D", v, t, nr, sk, q); put(n + "_S", mv, t[:, ::-1], mn, sk, q)
for k in [q[4:-2] for q in z.files if q.startswith("NAC|") and q.endswith("|v")]:
    v, t = z[f"NAC|{k}|v"], z[f"NAC|{k}|t"]
    for sd, sg in (("D", 1), ("S", -1)):
        me = bpy.data.meshes.new(f"nava_{k}_{sd}"); me.from_pydata((v * [sg, 1, 1]).tolist(), [], (t if sg > 0 else t[:, ::-1]).tolist()); me.materials.append(mat("PI (ARCU)")); me.update(); bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f_ in bm.faces: f_.smooth = True
        for e_ in bm.edges:
            if len(e_.link_faces) == 2 and e_.calc_face_angle(0) > .7: e_.smooth = False
        bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(f"nava_{k}_{sd}", me); o.parent = root; o.color = (.2, .8, .85, 1); c.objects.link(o)
sv = np.load(SKIN); sv, sf = sv["at_brat_fata_S__v"].astype(float), sv["at_brat_fata_S__f"]
src = bpy.data.objects["an_brat_fata_S"]; M = src.matrix_world; V = [M @ q.co + Vector((2400, 0, 0)) for q in src.data.vertices]; F = [p.vertices[:] for p in src.data.polygons]
for nm in ("an_usa_fata_S", "an_usa_spate_S", "an_nacela_inchis_S", "an_nacela_deschis_S"):
    o = bpy.data.objects[nm]; e = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = e.to_mesh(); b = len(V); V += [e.matrix_world @ q.co + Vector((2400, 0, 0)) for q in me.vertices]; F += [[b + i for i in p.vertices] for p in me.polygons]; e.to_mesh_clear()
bt = BVHTree.FromPolygons(V, F); cs = sv[sf].mean(1); zone = np.where((cs[:, 1] > 250) & (cs[:, 1] < 520) & (cs[:, 0] < -560) & (cs[:, 2] > 40))[0]; open_ = zone[[bt.find_nearest(Vector(p))[3] > .035 for p in cs[zone]]]; patch = set(open_.tolist())
for _ in range(3):                                                          # three rings over the lips
    vs = set(sf[list(patch)].ravel().tolist()); patch |= {int(i) for i in zone if any(int(q) in vs for q in sf[i])}
patch = np.array(sorted(patch)); pv, pi = np.unique(sf[patch], return_inverse=True); pf = pi.reshape(-1, 3); pc = sv[pv]; fnp = np.cross(pc[pf[:, 1]] - pc[pf[:, 0]], pc[pf[:, 2]] - pc[pf[:, 0]]); up = fnp.sum(0)[2] > 0; pf = pf if up else pf[:, ::-1]; pnr = np.zeros_like(pc); fnp = np.cross(pc[pf[:, 1]] - pc[pf[:, 0]], pc[pf[:, 2]] - pc[pf[:, 0]])
for i in range(3): np.add.at(pnr, pf[:, i], fnp)
pnr /= np.linalg.norm(pnr, axis=1)[:, None]; pc = pc - pnr * .03; print("PETIC fete", len(pf), "din care peste gaura", len(open_))
sk0 = z["BF varf|v"]; tb = sk0[sk0[:, 1] < sk0[:, 1].min() + 3]; mean = tb.mean(0); CP, CT = Vector((mean[0] * -1, float(np.percentile(sk0[:, 1], 0)) + 9.0, mean[2])), Vector((.12, .99, 0)).normalized()
if "tip_p" in z.files: t_ = z["tip_t"]; CP, CT = Vector((z["tip_p"] + t_ * 5) * [-1, 1, 1]), Vector(t_ * [-1, 1, 1])      # the arm ends 5 m inside the tip, on the tip's own back plane
for o in list(bpy.data.collections["ASAMBLAT_NOU"].all_objects):
    if o.name.startswith("an_brat_spate") or o.name.startswith("an_lacrima_brat"): continue
    q = "BF" if any(s in o.name for s in ("brat_fata", "nacela", "lama", "usa_fata", "usa_spate", "spinare", "R060")) else "PS"; d = o.copy(); d.name = "nava_" + o.name[3:]; c.objects.link(d); d.parent = root; d.matrix_parent_inverse = Matrix.Translation((2400, 0, 0))
    if o.name.startswith("an_brat_fata"):
        sg = 1 if o.name.endswith("_S") else -1; d.data = o.data.copy(); Mi = (Matrix.Translation((2400, 0, 0)) @ o.matrix_world).inverted(); bm = bmesh.new(); bm.from_mesh(d.data); bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Mi @ Vector((CP.x * sg, CP.y, CP.z)), plane_no=(Mi.to_3x3() @ Vector((CT.x * sg, CT.y, CT.z))).normalized(), clear_outer=True)
        nv = [bm.verts.new(Mi @ Vector((p[0] * sg, p[1], p[2]))) for p in pc]
        for f in pf: e = bm.faces.new([nv[i] for i in (f if sg > 0 else f[::-1])]); e.smooth = True
        bm.to_mesh(d.data); bm.free()
    if "lama" in o.name or "spinare" in o.name: d.color = (.55, .02, .03, 1); continue
    for i in range(len(d.material_slots)): d.material_slots[i].link = "OBJECT"; d.material_slots[i].material = mat(q)
    d.color = (*COLS[q], 1)
lab = bpy.data.objects.get("eticheta_ASAMBLAT_NOU_sus")
if lab: e = lab.copy(); e.data = lab.data.copy(); e.data.body = "NAVA COMPLETA"; e.name = "eticheta_NAVA_COMPLETA_sus"; e.location.x += X + 2400; lab.users_collection[0].objects.link(e)
keep = set(KEEP) | {"NAVA_COMPLETA"}
for o in list(bpy.data.objects):
    cn = {q.name for q in o.users_collection}
    if cn & keep or (o.name.startswith("eticheta_") and o.name[9:].replace("_sus", "") in keep): continue
    bpy.data.objects.remove(o, do_unlink=True)
for q in list(bpy.data.collections):
    if not q.all_objects: bpy.data.collections.remove(q)
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True); sc.frame_set(100)
for scr in bpy.data.screens:
    for ar in scr.areas:
        for sp in ar.spaces:
            if sp.type == "VIEW_3D": sp.shading.show_xray = False
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("COMPLETA", [(q.name, len(q.all_objects)) for q in bpy.data.collections], len(bpy.data.objects))
