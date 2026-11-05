# The new pieces' guides drawn afresh from their faired lines; the pieces stay. Usage: blender -b in --python nt_scoate_ghidaje.py -- out.blend <dir> id...
import bpy, sys, os, json, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, D = a[0], a[1]; GH = bpy.data.collections["GHIDAJE_NAVA"]; gm = bpy.data.materials["ghid_contur"]; XG = -4800.0
def draw(name, G, mx):
    if name in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[name])
    if not G.files: return
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.8; cu.materials.append(gm); names = []
    for k in G.files:
        P = G[k]; sp = cu.splines.new("POLY"); sp.points.add(len(P) - 1); names.append(k)
        for p, q in zip(sp.points, P): p.co = (mx * q[0], q[1], q[2], 1)
    o = bpy.data.objects.new(name, cu); GH.objects.link(o); o.location.x = XG; o["linii"] = json.dumps(names)
for i in a[2:]:
    G = np.load(os.path.join(D, i + "_g.npz")); c = bool(np.load(os.path.join(D, i + ".npz"))["central"])
    if c: draw("g_nt_%s_sudat" % i, G, 1)
    else: draw("g_nt_%s_sudat_D" % i, G, 1); draw("g_nt_%s_sudat_S" % i, G, -1)
print("GH", len(GH.objects)); bpy.context.scene.frame_set(1); bpy.ops.wm.save_as_mainfile(filepath=OUT)
