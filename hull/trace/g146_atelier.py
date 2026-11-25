# Work block for nt_146, separate from the assembled ship: reference + new guides, new piece + guides, guides alone, at x -9600 / -11000 / -12400. Usage: blender -b <in> --python g146_atelier.py -- <out.blend> <dir>
import bpy, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, D = a[0], a[1]; PF, XP = os.environ.get("PREF", "at146"), float(os.environ.get("XP", "-11000"));   # PREF/XP: a second version beside the first, the first kept
Z = np.load(D + "/146.npz"); G = np.load(D + "/146_g.npz")
col = bpy.data.collections.get("ATELIER_146") or bpy.data.collections.new("ATELIER_146")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for o in [o for o in col.objects if o.name.startswith(PF + "_")]: bpy.data.objects.remove(o)
gc = bpy.data.materials.get("ghid_contur") or bpy.data.materials.new("ghid_contur"); gc.diffuse_color = (.1, .8, .2, 1); gr = bpy.data.materials.get("ghid_coasta") or bpy.data.materials.new("ghid_coasta"); gr.diffuse_color = (.95, .35, .1, 1)
def guides(name, x):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = .7; cu.materials.append(gc); cu.materials.append(gr)
    for k in G.files:
        P = G[k]; sp = cu.splines.new("POLY"); sp.points.add(len(P) - 1); sp.material_index = 1 if k.startswith("coasta") else 0
        for p, q in zip(sp.points, P): p.co = (float(q[0]), float(q[1]), float(q[2]), 1)
    o = bpy.data.objects.new(name, cu); col.objects.link(o); o.location.x = x; return o
R = bpy.data.objects["R005_146_C"] if "R005_146_C" in bpy.data.objects else [o for o in bpy.data.objects if o.name.startswith("R005")][0]
if "at146_referinta" not in bpy.data.objects: rc = R.copy(); rc.data = R.data; rc.name = "at146_referinta"; col.objects.link(rc); rc.matrix_world = R.matrix_world; rc.location.x = R.location.x - 9600
me = bpy.data.meshes.new(PF + "_piesa"); me.from_pydata(Z["v"].tolist(), [], Z["f"].tolist()); me.validate(); me.materials.append(bpy.data.materials["Material_8"]); o = bpy.data.objects.new(PF + "_piesa", me); col.objects.link(o); o.location.x = XP
for s in bpy.context.selected_objects: s.select_set(False)
bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.shade_smooth_by_angle(angle=0.5); o.select_set(False)
guides(PF + "_ghidaje_pe_ref", -9600) if PF == "at146" else None; g2 = guides(PF + "_ghidaje_pe_piesa", XP); guides(PF + "_ghidaje", XP - 1400)
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SALVAT", OUT)
