# The scraps' bodies in the moving pieces' way taken out of nt_marunte_S, D = its mirror again. Usage: blender -b f --python nt_marunte_taie.py -- <out.blend> <loc.npz>
import bpy, sys, numpy as np, bmesh
a = sys.argv[sys.argv.index("--") + 1:]; Z = np.load(a[1]); lab, hit = Z["lab"], set(Z["hit"].tolist()); S = bpy.data.objects["nt_marunte_S"]; D = bpy.data.objects["nt_marunte_D"]
for o, l in ((S, lab), (D, lab)):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); assert len(bm.verts) == len(l)
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in range(len(l)) if int(l[i]) in hit], context="VERTS"); bm.to_mesh(o.data); bm.free(); print("TAIAT", o.name, len(o.data.polygons))
bpy.context.scene.frame_set(1); bpy.ops.wm.save_as_mainfile(filepath=a[0])
