# One object split into named parts by face lists (ps_sus_jos.py): each part its own object (own mesh, same material,
# transform and collection); the original object removed (its mesh stays if other objects use it - PS keeps it).
# Usage: blender -b <in> --python sparge_piesa.py -- <out.blend> <parts.npz> <obj> <part=name ...>
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, P, NAME = a[0], np.load(a[1]), a[2]; parts = [s.split("=") for s in a[3:]]
o = bpy.data.objects[NAME]; cols = list(o.users_collection)
for key, nm in parts:
    keep = set(P[key].tolist()); bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[fc for fc in bm.faces if fc.index not in keep], context="FACES")
    me = bpy.data.meshes.new(nm); bm.to_mesh(me); bm.free()
    for m in o.data.materials: me.materials.append(m)
    n = bpy.data.objects.new(nm, me); n.matrix_world = o.matrix_world.copy()
    for c in cols: c.objects.link(n)
    print("PIESA %s: %d fete" % (nm, len(me.polygons)))
bpy.data.objects.remove(o); bpy.ops.wm.save_as_mainfile(filepath=OUT)
