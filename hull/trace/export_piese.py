# The scene's pieces exported in world coordinates (bmesh, triangulated, vertex order kept): <name>__v / <name>__f per object.
# Usage: blender -b <f.blend> --python export_piese.py -- <out.npz> [object ...]   (default: the PS + arms + nacelles set)
import bpy, bmesh, numpy as np, sys
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; d = {}
names = a[1:] or ["PS", "brat_spate_S", "brat_spate_D", "capac_086", "comp_055_S", "comp_055_D", "brat_fata_S", "brat_fata_D", "nacela_rosie_S", "nacela_rosie_D"]
for n in names:
    o = bpy.data.objects.get(n)
    if o is None: print("LIPSA", n); continue
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); bmesh.ops.triangulate(bm, faces=bm.faces); bm.verts.index_update()
    v = np.array([x.co[:] for x in bm.verts]); f = np.array([[x.index for x in t.verts] for t in bm.faces]); d[n + "__v"] = v; d[n + "__f"] = f
    print("EXP", n, v.shape, f.shape, v.min(0).round(), v.max(0).round())
np.savez(out, **d)
