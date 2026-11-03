# The animated workshop shows only our moving blades (asked: at_PS had both fixed and moving blades - drawn more than needed): the
# reference blade copies ref_lama_* are removed from ATELIER_LAME (the reference itself stays in REFERINTA).
# Usage: blender -b <in.blend> --python sterge_ref_din_atelier.py -- <out.blend>
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]; n = 0
for o in list(bpy.data.collections["ATELIER_LAME"].objects):
    if o.name.startswith("ref_lama"): bpy.data.objects.remove(o); n += 1
print("STERSE %d copii ale lamelor de referinta din ATELIER_LAME" % n); bpy.ops.wm.save_as_mainfile(filepath=OUT)
