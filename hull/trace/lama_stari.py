# Board cleaned for the blade decision (asked: blade an_lama_S/D kept, hinge further back - at y PY - , the root corner stays hidden
# in PS; clean the board to judge exactly): removes the rejected nacelle variant (an_lama_nacela_*, lama_nacela_separat_S,
# GHIDAJ_LAMA_NACELA) and the old stowed previews (*_strans); adds collection LAMA_STARI with lama_stransa_S / _D = the blade turned
# ANG deg about the vertical through the hinge (-59.6, PY, 291.9) (D mirrored), and empties balama_lama_S / _D marking the hinges.
# PX: the hinge's x for the S blade (the D one mirrored) - the hinge that lands the stowed root where asked may lie past the axis.
# SL=x,y,z SD=m: after the turn the stowed blade also slides SD m along SL (S side; D mirrored) - turn + slide.
# Usage: blender -b <in.blend> --python lama_stari.py -- <out.blend> ; env PY=161 ANG=22 PX=-59.6 X0=-1600 SL= SD=0
import bpy, sys, os, math
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]; E = lambda k, d: float(os.environ.get(k, d)); PY, ANG, X0, PX = E("PY", 161), E("ANG", 22), E("X0", -1600), E("PX", -59.6); SD = E("SD", 0)
SL = Vector([float(q) for q in os.environ["SL"].split(",")]).normalized() if os.environ.get("SL") else Vector((0, 0, 0))
gone = [o.name for o in bpy.data.objects if o.name.startswith(("an_lama_nacela", "lama_nacela_separat", "marcaj_balama_", "eticheta_")) or o.name.endswith("_strans") or o.name.startswith(("lama_stransa_", "balama_lama_"))]
for cn in ("BALAMALE_INCERCATE",):
    cc = bpy.data.collections.get(cn)
    if cc: [bpy.data.objects.remove(o) for o in list(cc.objects)]; bpy.data.collections.remove(cc)
c = bpy.data.collections.get("GHIDAJ_LAMA_NACELA")
if c: gone += [o.name for o in c.objects]
for n in set(gone):
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n])
if c: bpy.data.collections.remove(c)
col = bpy.data.collections.get("LAMA_STARI") or bpy.data.collections.new("LAMA_STARI")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for sd, sg in (("S", 1), ("D", -1)):
    src = bpy.data.objects["an_lama_" + sd]; P = Vector((sg * PX + X0, PY, 291.9))
    o = bpy.data.objects.new("lama_stransa_" + sd, src.data.copy()); col.objects.link(o)
    sl = Vector((SL.x * sg, SL.y, SL.z)) * SD
    o.matrix_world = Matrix.Translation(sl) @ Matrix.Translation(P) @ Matrix.Rotation(math.radians(sg * ANG), 4, "Z") @ Matrix.Translation(-P) @ src.matrix_world
    e = bpy.data.objects.new("balama_lama_" + sd, None); e.empty_display_type = "SINGLE_ARROW"; e.empty_display_size = 40; e.location = P; col.objects.link(e)
print("STARI: sterse %d obiecte, lama_stransa_S/D rotite %+.1f grade in jurul balamalei la x %.1f y %.1f (S), apoi alunecare %.0f m pe %s" % (len(set(gone)), ANG, PX, PY, SD, tuple(round(v, 3) for v in SL)))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
