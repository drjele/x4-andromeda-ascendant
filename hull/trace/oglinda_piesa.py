# Polish: a piece made the exact mirror of its pair (symmetry rule: the left one = the mirror of the right one): the target object's
# mesh replaced by the source's, mirrored in x (faces reversed), materials and UVs kept, its place kept.
# Usage: blender -b <f.blend> --python oglinda_piesa.py -- <out.blend> <source obj> <target obj> ...(pairs)
import bpy, sys, bmesh
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]
for src, dst in zip(a[1::2], a[2::2]):
    s, d = bpy.data.objects[src], bpy.data.objects[dst]; me = s.data.copy(); me.name = dst
    bm = bmesh.new(); bm.from_mesh(me)
    for v in bm.verts: v.co.x = -v.co.x - 2 * 1600 * 0          # (mesh in ship coords around x = 0: mirrored about the ship's middle)
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
    old = d.data; d.data = me; bpy.data.meshes.remove(old) if old.users == 0 else None; print("OGLINDA", src, "->", dst, len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
