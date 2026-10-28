# Draw the flat guide line (ghid_plan2.py) in Blender: one closed curve in ONE horizontal plane (z = Z), on the exploded
# reference (its middle at the reference's x) and on the exploded new piece; plus an overlay copy of the new piece moved
# onto the exploded reference (blue, see-through) to compare the two shapes. Collection GHIDAJE_PLAN_169_C.
# Usage: blender -b <file.blend> --python ghid_plan_draw.py -- <ghid.npz> <out.blend> [z]
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; G = np.load(a[0]); OUT = a[1]; Z = float(a[2]) if len(a) > 2 else 362.0
g, cen = G["contur"], float(G["centru"])
er, orr = bpy.data.objects["expl_R002 169_C"], bpy.data.objects["R002 169_C"]; xr = cen + (er.location.x - orr.location.x)
en, on = bpy.data.objects["expl_piesa_comp_169_C"], bpy.data.objects["piesa_comp_169_C"]; xn = -1700.0 + (en.location.x - on.location.x)
col = bpy.data.collections.get("GHIDAJE_PLAN_169_C") or bpy.data.collections.new("GHIDAJE_PLAN_169_C")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for ob in list(col.objects): bpy.data.objects.remove(ob)
mg = bpy.data.materials.get("ghidaj") or bpy.data.materials.new("ghidaj"); mg.diffuse_color = (1.0, 0.85, 0.0, 1)
for nm, x0 in (("ghid_plan_169_ref", xr), ("ghid_plan_169_nou", xn)):
    cu = bpy.data.curves.new(nm, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.2; sp = cu.splines.new("POLY"); sp.points.add(len(g) - 1); sp.use_cyclic_u = True
    for p, (x, y) in zip(sp.points, g): p.co = (x + x0, y, Z, 1)
    cu.materials.append(mg); col.objects.link(bpy.data.objects.new(nm, cu))
cp = en.copy(); cp.data = en.data; cp.name = "suprapus_piesa_169_C_pe_ref"; cp.location.x += xr - xn; col.objects.link(cp)
mb = bpy.data.materials.get("suprapus") or bpy.data.materials.new("suprapus"); mb.diffuse_color = (0.1, 0.35, 1.0, 0.45)
cp.material_slots[0].link = "OBJECT"; cp.material_slots[0].material = mb
print("GHID PLAN: z %.0f, pe referinta la x %.1f, pe piesa noua la x %.1f; copie suprapusa pe referinta" % (Z, xr, xn))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
