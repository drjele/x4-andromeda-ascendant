# Guide lines from an npz (each array = one polyline, ship coordinates centred) drawn at x + X0 into a collection, after
# removing what is named (objects whose name starts with a prefix). Colour by name: contur* green, the rest red.
# Usage: blender -b <f.blend> --python ghidaje_npz_draw.py -- <out.blend> <guides.npz> <x0> <collection> <prefix> [remove-prefix ...]
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, G, X0, COL, PRE = a[0], np.load(a[1]), float(a[2]), a[3], a[4]; sc = bpy.context.scene
gone = [o.name for o in bpy.data.objects if any(o.name.startswith(p) for p in a[5:])]
for n in gone: bpy.data.objects.remove(bpy.data.objects[n])
col = bpy.data.collections.get(COL) or bpy.data.collections.new(COL)
if col.name not in sc.collection.children: sc.collection.children.link(col)
def mat(n, c):
    m = bpy.data.materials.get(n) or bpy.data.materials.new(n); m.diffuse_color = c; return m
for k in G.files:
    P = G[k]; cu = bpy.data.curves.new(PRE + k, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.8; sp = cu.splines.new("POLY"); sp.points.add(len(P) - 1)
    for p, q in zip(sp.points, P): p.co = (q[0] + X0, q[1], q[2], 1)
    if k.startswith("contact_"): cu.materials.append(mat("ghid_contact", (1, 0.85, 0.05, 1)))            # joint guides:
    elif k.startswith("pri_"): cu.materials.append(mat("ghid_principal", (0.05, 0.85, 1, 1)))             # contact yellow,
    elif k.startswith("sec_"): cu.materials.append(mat("ghid_secundar", (1, 0.1, 0.85, 1)))              # bands cyan/magenta
    elif k.startswith("perp_"): cu.materials.append(mat("ghid_perpendicular", (1, 0.85, 0.05, 1)))        # normals yellow
    else: cu.materials.append(mat("ghid_contur", (0.1, 0.8, 0.2, 1)) if k.startswith(("contur", "spinare")) else mat("ghid_sus", (1, 0.1, 0.1, 1)))
    o = bpy.data.objects.new(PRE + k, cu); col.objects.link(o); o.color = tuple(cu.materials[0].diffuse_color)
print("GHIDAJE: %d scoase (%s...), %d desenate la x %+.0f in %s" % (len(gone), ", ".join(gone[:3]), len(G.files), X0, COL))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
