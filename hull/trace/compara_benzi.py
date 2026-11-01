# Two bands side by side for comparison (asked: our band and lucru_brat_fata's, separately, one above the other with a gap): each band
# mesh + its three lines (exterior / spine-centre / interior) drawn as thin tubes, the first at (X0, 0, 0), the second at (X0, 0, DZ),
# in collection COMPARATIE_BENZI.
# Usage: blender -b <f.blend> --python compara_benzi.py -- <out.blend> <x0> <dz> <band npz:v:f> <lines npz:ext,spine,int> <rgb>
#        <band2 ...> <lines2 ...> <rgb2>
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, X0, DZ = a[0], float(a[1]), float(a[2])
col = bpy.data.collections.get("COMPARATIE_BENZI") or bpy.data.collections.new("COMPARATIE_BENZI")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
def mat(n, c):
    m = bpy.data.materials.get(n) or bpy.data.materials.new(n); m.diffuse_color = c; m.use_fake_user = True; return m
for idx, (bspec, lspec, rgb) in enumerate(((a[3], a[4], a[5]), (a[6], a[7], a[8]))):
    off = (X0, 0, DZ * idx); c = [float(q) for q in rgb.split(",")] + [1]; tag = "noua" if idx == 0 else "referinta"
    p, kv, kf = bspec.split(":"); Z = np.load(p)
    me = bpy.data.meshes.new("banda_" + tag); me.from_pydata(Z[kv].tolist(), [], Z[kf].tolist()); me.validate(); me.materials.append(mat("banda_" + tag, c))
    o = bpy.data.objects.new("cmp_banda_" + tag, me); col.objects.link(o); o.location = off; o.color = c
    p, keys = lspec.split(":"); Z = np.load(p)
    for k, lc in zip(keys.split(","), ((0.1, 0.8, 0.1, 1), (0.05, 0.05, 0.05, 1), (0.1, 0.8, 0.1, 1))):
        L = Z[k]; cu = bpy.data.curves.new("cmp_" + tag + "_" + k, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.5
        sp = cu.splines.new("POLY"); sp.points.add(len(L) - 1)
        for i, q in enumerate(L): sp.points[i].co = (q[0], q[1], q[2], 1)
        cu.materials.append(mat("cmp_linie_%d" % (0 if "spin" in k or "centru" in k else 1), lc))
        ob = bpy.data.objects.new("cmp_" + tag + "_" + k, cu); col.objects.link(ob); ob.location = off; ob.color = lc
print("COMPARATIE: 2 benzi la x %.0f, a doua cu %.0f m mai sus" % (X0, DZ)); bpy.ops.wm.save_as_mainfile(filepath=OUT)
