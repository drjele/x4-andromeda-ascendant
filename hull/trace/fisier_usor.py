# A light working file (the full one froze the computer: every version kept at ~1M faces): an empty scene with only the
# materials taken from the full file, saved, so asamblare_completa.py can put the game-weight pieces in it.
# Usage: blender -b --factory-startup --python fisier_usor.py -- <full.blend> <out.blend> <material> ...
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; SRC, OUT, MATS = a[0], a[1], a[2:]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
with bpy.data.libraries.load(SRC, link=False) as (src, dst): dst.materials = [m for m in src.materials if m in MATS]
for m in bpy.data.materials:
    m.use_fake_user = True                                              # kept on save though nothing uses them yet
for im in bpy.data.images: print("IMAGINE", im.name, "impachetata" if im.packed_file else "LIPSA", tuple(im.size))   # packed with
                                                                        # the materials already (re-packing an image with no path lost it)
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("USOR", OUT, [m.name for m in bpy.data.materials])
