# The whole blade replaced by its two halves (asked: hinge on the blade at its middle, each half folds into the arm on its own):
# removes an_lama_S/D, lama_separat_S, lama_stransa_S/D, balama_lama_S/D before the halves are built.
# Usage: blender -b <in.blend> --python sterge_lama_intreaga.py -- <out.blend>
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]
for n in ("an_lama_S", "an_lama_D", "lama_separat_S", "lama_stransa_S", "lama_stransa_D", "balama_lama_S", "balama_lama_D"):
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n])
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("STERS lama intreaga")
