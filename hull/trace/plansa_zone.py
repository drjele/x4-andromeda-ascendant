# Board block ZONE_COMPONENTE: one object and one colour per component (zone_curate.npz). Usage:
# blender -b <scene> --python plansa_zone.py -- <npz> <x> <out.blend>
import bpy, sys, os, numpy as np
NPZ, X, OUT = sys.argv[sys.argv.index("--") + 1:][:3]; assert not os.path.exists(OUT)
COLS = {"PS": (.85, .85, .85), "BF": (.95, .75, .1), "BS": (.45, .28, .12), "BJ": (.1, .25, .9), "PI (ARCU)": (.15, .7, .15), "CORP": (.8, .08, .08), "CORP etaj": (1, .42, .05), "AI": (.05, .65, .7), "AS": (.95, .35, .65), "H": (.45, .1, .75)}
z = np.load(NPZ); c = bpy.data.collections.new("ZONE_COMPONENTE"); bpy.context.scene.collection.children.link(c)
for q in COLS:
    T = z["T"][z["zone"] == q]; V, I = np.unique(T.reshape(-1, 3).round(3), axis=0, return_inverse=True); F = I.reshape(-1, 3); F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
    n = "zona_" + q.replace(" (ARCU)", "").replace(" ", "_"); me = bpy.data.meshes.new(n); me.from_pydata(V.tolist(), [], F.tolist()); m = bpy.data.materials.new(n); m.diffuse_color = (*COLS[q], 1); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*COLS[q], 1); me.materials.append(m); o = bpy.data.objects.new(n, me); o.location.x = float(X); c.objects.link(o)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("PLANSA", [o.name for o in c.objects])
