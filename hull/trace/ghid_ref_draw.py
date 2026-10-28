# Draw the reference guide lines (ghid_ref_contur.py: the outer line and the inner U, straight sides + one arc at each
# meeting) on the exploded reference body: moved like expl_R002 169_C, each point at the height of the reference's top
# surface there (highest shell point within 4 m, smoothed). Collection GHIDAJE_REF_169_C; earlier guides left alone.
# Usage: blender -b <file.blend> --python ghid_ref_draw.py -- <ghid_ref169.npz> <esantion_punte.npz> <out.blend>
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; G = np.load(a[0]); S = np.load(a[1]); OUT = a[2]
e, o = bpy.data.objects["expl_R002 169_C"], bpy.data.objects["R002 169_C"]; off = np.array(e.location - o.location)
Q = S["ps"]
col = bpy.data.collections.get("GHIDAJE_REF_169_C") or bpy.data.collections.new("GHIDAJE_REF_169_C")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for ob in list(col.objects): bpy.data.objects.remove(ob)
mg = bpy.data.materials.get("ghidaj") or bpy.data.materials.new("ghidaj"); mg.diffuse_color = (1.0, 0.85, 0.0, 1)
for key in ("outer", "inner"):
    L = G[key]; z = []
    for x, y in L:
        m = (np.abs(Q[:, 0] - x) < 4) & (np.abs(Q[:, 1] - y) < 4); z.append(Q[m, 2].max() if m.any() else np.nan)
    z = np.array(z); g = ~np.isnan(z); z = np.interp(np.arange(len(z)), np.nonzero(g)[0], z[g])
    k = np.exp(-0.5 * (np.arange(-12, 13) / 4.0) ** 2); k /= k.sum(); z = np.convolve(np.pad(z, 12, mode="edge"), k, "valid") + 1.5
    cu = bpy.data.curves.new(key, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.2; sp = cu.splines.new("POLY"); sp.points.add(len(L) - 1)
    for p, (x, y), zz in zip(sp.points, L, z): p.co = (x + off[0], y + off[1], zz + off[2], 1)
    cu.materials.append(mg); col.objects.link(bpy.data.objects.new("ghid_ref_169_" + ("exterior" if key == "outer" else "interior_U"), cu))
print("GHIDAJE REF 169_C desenate pe expl_R002 169_C (deplasare %s)" % np.round(off).tolist())
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
