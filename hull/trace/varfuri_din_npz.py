# New vertex positions for existing objects, everything else kept (materials, UVs, vertex order): obj=key from an npz of
# world coordinates (taken into each object's own frame). Usage: blender -b <f.blend> --python varfuri_din_npz.py -- <out.blend> <file.npz> <obj=key[!]> ... (! = also reverse the faces)
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, Z = a[0], np.load(a[1])
for spec in a[2:]:
    n, k = spec.rstrip("!").split("="); o = bpy.data.objects[n]; M = np.linalg.inv(np.array(o.matrix_world))   # world -> object
    V = Z[k].astype(float); V = (np.c_[V, np.ones(len(V))] @ M.T)[:, :3].astype(np.float32)
    assert len(V) == len(o.data.vertices), n
    o.data.vertices.foreach_set("co", V.ravel()); o.data.update(); print("VARFURI", n, len(V))
import bmesh
for spec in [x_ for x_ in a[2:] if x_.endswith("!")]:   # obj=key! : also turn the faces (they faced inwards)
    o = bpy.data.objects[spec.split("=")[0]]; bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free(); print("INTORS", o.name)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
