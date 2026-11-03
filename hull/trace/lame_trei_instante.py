# Three instances of the blade workshop (asked: one with the blades extended, one retracted, one animated folding): the animated
# ATELIER_LAME stays at x XB; ATELIER_DESCHISE (x XB + DX1) and ATELIER_STRANSE (x XB + DX2) = copies of every workshop piece, the
# blades frozen at the open frame FO / the stowed frame FS (their world matrix at that frame, no animation); the reference blades are
# left out of the copies. Usage: blender -b <in.blend> --python lame_trei_instante.py -- <out.blend> ; env XB=-7000 DX1=-2000 DX2=-4000 FO=100 FS=1
import bpy, sys, os
from mathutils import Matrix, Vector
OUT = sys.argv[sys.argv.index("--") + 1]; E = lambda k, d: float(os.environ.get(k, d))
XB, DX1, DX2, FO, FS = E("XB", -7000), E("DX1", -2000), E("DX2", -4000), int(E("FO", 100)), int(E("FS", 1))
sc = bpy.context.scene; src = [o for o in bpy.data.collections["ATELIER_LAME"].objects if not o.name.startswith("ref_lama")]
for cname, dx, fr in (("ATELIER_DESCHISE", DX1, FO), ("ATELIER_STRANSE", DX2, FS)):
    old = bpy.data.collections.get(cname)
    if old:
        for o in list(old.objects): bpy.data.objects.remove(o)
        bpy.data.collections.remove(old)
    col = bpy.data.collections.new(cname); sc.collection.children.link(col); sc.frame_set(fr)
    for o in src:
        c = bpy.data.objects.new(o.name.replace("at_", "d_" if cname.endswith("DESCHISE") else "s_", 1), o.data); col.objects.link(c)
        c.matrix_world = Matrix.Translation(Vector((dx, 0, 0))) @ o.matrix_world; c.color = o.color
    print("INSTANTA %s: %d obiecte la x %+.0f fata de atelier, cadrul %d" % (cname, len(src), dx, fr))
sc.frame_set(FO); bpy.ops.wm.save_as_mainfile(filepath=OUT)
