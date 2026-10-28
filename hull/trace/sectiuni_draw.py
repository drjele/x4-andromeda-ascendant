# Draw the section contours (sectiuni_spline.py) on the exploded reference: every EVERY m one station, each contour a
# closed flat line in its own plane (y constant), plus the confirmed top silhouette (outer B and inner U at the top of
# the deck); one collection per variant (the first visible, the others hidden), placed like expl_R002 169_C.
# Usage: blender -b <f.blend> --python sectiuni_draw.py -- <out.blend> <ghid_drept2.npz> <sectiuni_a.npz>[,<b.npz>...] [every]
import bpy, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, GN = a[0], a[1]; FILES = a[2].split(","); EVERY = float(a[3]) if len(a) > 3 else 20.0
CEN = -4.68; er, orr = bpy.data.objects["expl_R002 169_C"], bpy.data.objects["R002 169_C"]; X0 = CEN + (er.location.x - orr.location.x)
def curve(col, nm, P3, cyc, color):
    cu = bpy.data.curves.new(nm, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.6; sp = cu.splines.new("POLY"); sp.points.add(len(P3) - 1); sp.use_cyclic_u = cyc
    for p, q in zip(sp.points, P3): p.co = (q[0] + X0, q[1], q[2], 1)
    m = bpy.data.materials.get(nm[:20] + str(color)) or bpy.data.materials.new(nm[:20] + str(color)); m.diffuse_color = color; cu.materials.append(m)
    col.objects.link(bpy.data.objects.new(nm, cu))
for i, fn in enumerate(FILES):
    Z = np.load(fn); tag = os.path.basename(fn)[:-4].replace("sectiuni_", ""); cname = "SECTIUNI_169_C_" + tag
    col = bpy.data.collections.get(cname) or bpy.data.collections.new(cname)
    if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
    for o in list(col.objects): bpy.data.objects.remove(o)
    ys = Z["ys"]; n = 0
    for y in ys:
        if abs(((ys[0] - y) / EVERY) - round((ys[0] - y) / EVERY)) > 1e-6: continue
        sel = np.nonzero(np.abs(Z["sy"] - y) < 1e-3)[0]
        for j, c in enumerate(sel):
            F = Z["pts"][Z["start"][c]:Z["start"][c + 1]]; curve(col, "sec_%s_y%d_%d" % (tag, int(round(y)), j), np.stack([F[:, 0], np.full(len(F), y), F[:, 1]], 1), True, (1.0, 0.75, 0.0, 1)); n += 1
    if i: bpy.context.view_layer.layer_collection.children[cname].hide_viewport = True
    print("SECTIUNI %s: %d contururi (o statie la %.0f m), %s" % (tag, n, EVERY, "vizibile" if i == 0 else "ascunse"))
G = np.load(GN); col = bpy.data.collections.get("SILUETA_169_C") or bpy.data.collections.new("SILUETA_169_C")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
for k in ("B", "B_int"):
    Q = G[k]; curve(col, "silueta_" + ("exterior" if k == "B" else "interior"), np.stack([Q[:, 0], Q[:, 1], np.full(len(Q), 362.0)], 1), False, (0.1, 0.4, 1.0, 1))
if len(a) > 4:                                                         # the long guide lines through the sections (rails)
    Rr = np.load(a[4]); col = bpy.data.collections.get("GHIDAJE_SECTIUNI_169_C") or bpy.data.collections.new("GHIDAJE_SECTIUNI_169_C")
    if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
    for o in list(col.objects): bpy.data.objects.remove(o)
    cols = {"ps_sus": (0.0, 0.7, 0.0, 1), "ps_jos": (0.6, 0.0, 0.6, 1), "ps_lat": (0.9, 0.0, 0.0, 1), "br_ext": (0.9, 0.0, 0.0, 1), "br_int": (0.1, 0.4, 1.0, 1), "br_sus": (0.0, 0.7, 0.0, 1), "br_jos": (0.6, 0.0, 0.6, 1)}
    for k, c in cols.items():
        Q = Rr[k]
        for sd, sg in (("D", 1), ("S", -1)):
            if k in ("ps_sus", "ps_jos") and sg < 0: continue
            curve(col, "ghid_%s%s" % (k, "" if k in ("ps_sus", "ps_jos") else "_" + sd), Q * [sg, 1, 1], False, c)
    print("GHIDAJE longitudinale: %d linii" % len(col.objects))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
