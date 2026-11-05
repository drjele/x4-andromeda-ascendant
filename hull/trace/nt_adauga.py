# Built pieces added to NAVA_TERMINATA (x -7200), each its own object, S = mirror of the D base, guides welded per component in GHIDAJE_NAVA
# (x -4800). A central piece gets one object. Usage: blender -b <in> --python nt_adauga.py -- <out.blend> <dir> id [id...]   env CORP=1 uses the id only.
import bpy, sys, os, json, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, D = a[0], a[1]; NT = bpy.data.collections["NAVA_TERMINATA"]; GH = bpy.data.collections["GHIDAJE_NAVA"]; XN, XG = -7200.0, -4800.0
gm = bpy.data.materials.get("ghid_contur") or bpy.data.materials.new("ghid_contur"); gm.diffuse_color = (.1, .8, .2, 1)
def piece(name, v, f, uv, mat, flip):
    for n in (name,):
        if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n])
    me = bpy.data.meshes.new(name); me.from_pydata(v.tolist(), [], f.tolist()); me.validate(); m = bpy.data.materials.get(mat) or bpy.data.materials["Material_8"]; me.materials.append(m)
    L = me.uv_layers.new(name="UVMap"); li = np.zeros(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", li); L.data.foreach_set("uv", uv[li].ravel())
    o = bpy.data.objects.new(name, me); NT.objects.link(o); o.location.x = XN; o.color = (.75, .75, .78, 1)
    for s in bpy.context.selected_objects: s.select_set(False)
    bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.shade_smooth_by_angle(angle=0.436); o.select_set(False)
def guides(name, G, mx):
    if not G.files: return
    if name in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[name])
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.8; cu.materials.append(gm); names = []
    for k in G.files:
        P = G[k]; P = P[::max(1, len(P) // 400)]; sp = cu.splines.new("POLY"); sp.points.add(len(P) - 1); names.append(k)
        for p, q in zip(sp.points, P): p.co = (mx * q[0], q[1], q[2], 1)
    o = bpy.data.objects.new(name, cu); GH.objects.link(o); o.location.x = XG; o["linii"] = json.dumps(names)
for id_ in a[2:]:
    Z = np.load(os.path.join(D, id_ + ".npz")); v = Z["v"].astype(float); f = Z["f"]; uv = Z["uv"]; mat = str(Z["mat"]); c = bool(Z["central"]); G = np.load(os.path.join(D, id_ + "_g.npz"))
    if c: piece("nt_" + id_, v, f, uv, mat, False); guides("g_nt_%s_sudat" % id_, G, 1)
    else:
        piece("nt_%s_D" % id_, v, f, uv, mat, False); guides("g_nt_%s_sudat_D" % id_, G, 1)
        w = v * [-1, 1, 1]; piece("nt_%s_S" % id_, w, f[:, ::-1], uv * [-1, 1] + [1, 0], mat, True); guides("g_nt_%s_sudat_S" % id_, G, -1)
    jp = os.path.join(D, id_ + ".json")
    if os.path.exists(jp):
        ms = sorted(set(r["metoda"] for r in json.load(open(jp))["rows"]))
        for n in (("nt_" + id_,) if c else ("nt_%s_D" % id_, "nt_%s_S" % id_)): bpy.data.objects[n]["metoda"] = ",".join(ms)
    print("ADAUGAT", id_, mat, len(f))
VAL = os.environ.get("VAL")                                                   # the validated pieces' own guides, read off them (nt_ghidaje_val.py)
if VAL:
    for fn in sorted(os.listdir(VAL)):
        if fn.endswith("_vg.npz"): guides("g_nt_%s_sudat" % fn[:-7], np.load(os.path.join(VAL, fn)), 1)
print("BLOC ghidaje:", len([o for o in GH.objects if o.type == "CURVE"]), "piese:", len(NT.objects))
bpy.context.scene.frame_set(1); bpy.ops.wm.save_as_mainfile(filepath=OUT)
