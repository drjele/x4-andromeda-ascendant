# Draw the guide outlines (ghid_contur.py) as closed poly curves: reference pieces (names starting with "expl_R") in
# yellow in GHIDAJE_REF, new pieces in cyan in GHIDAJE_NOU; one curve per outline, named ghid_<piece>_<view>.
# Usage: blender -b <file.blend> --python ghid_draw.py -- <contururi.npz> <out.blend>
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; D = np.load(a[0]); OUT = a[1]; sc = bpy.context.scene
def coll(n):
    c = bpy.data.collections.get(n) or bpy.data.collections.new(n)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    for o in list(c.objects): bpy.data.objects.remove(o)
    return c
cr, cn = coll("GHIDAJE_REF"), coll("GHIDAJE_NOU")
def mat(n, c):
    m = bpy.data.materials.get(n) or bpy.data.materials.new(n); m.diffuse_color = c; return m
mr, mn = mat("ghidaj_ref", (1.0, 0.85, 0.0, 1)), mat("ghidaj_nou", (0.0, 0.9, 1.0, 1))
for key in D.files:
    piece, view, i = key.split("|"); P = D[key]; ref = piece.startswith("expl_R")
    cu = bpy.data.curves.new("ghid", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.6; sp = cu.splines.new("POLY"); sp.points.add(len(P) - 1); sp.use_cyclic_u = True
    for p, q in zip(sp.points, P): p.co = (q[0], q[1], q[2], 1)
    cu.materials.append(mr if ref else mn)
    o = bpy.data.objects.new("ghid_%s_%s%s" % (piece.replace("expl_", ""), view, "" if i == "0" else "_" + i), cu); (cr if ref else cn).objects.link(o)
print("GHIDAJE: %d referinta, %d noi" % (len(cr.objects), len(cn.objects)))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
