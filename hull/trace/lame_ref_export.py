# The reference blades' S halves exported for the clean rebuild (asked: our blades must follow the reference blades' angles - all
# of them): per Circle.* (lame_rosu) the triangles with x < 0, world (= ship) coords, to <out.npz> as tri_<name>.
# Usage: blender -b <scene> --python lame_ref_export.py -- <out.npz>
import bpy, bmesh, sys, numpy as np
OUT = sys.argv[sys.argv.index("--") + 1]; out = {}
for o in sorted(bpy.data.objects, key=lambda q: q.name):
    if not o.name.startswith("Circle") or o.type != "MESH": continue
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); bmesh.ops.triangulate(bm, faces=bm.faces)
    T = np.array([[v.co[:] for v in f.verts] for f in bm.faces if f.calc_center_median().x < 0]); out["tri_" + o.name.replace(".", "_")] = T; print("EXP", o.name, T.shape)
np.savez(OUT, **out)
