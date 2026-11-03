# The blade's fold animation (asked: one rotation from hinge 7, animate it and say how to play it): an_lama_S / an_lama_D get their
# origin on the hinge (mesh moved by -hinge, object placed at the hinge; nothing moves on screen), then keyframes on the rotation
# about the vertical: frame 1 stowed (S +A, D -A), frame F deployed (0), frame 2F stowed again; smooth (Bezier, auto-clamped).
# Removes the old helpers (LAMA_STARI, stowed previews, hinge markers). Scene frame range 1..2F.
# Usage: blender -b <in.blend> --python lama_anim.py -- <out.blend> <hx,hy,hz> <A deg> ; env F=60 X0=-1600
import bpy, sys, os, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; hx, hy, hz = (float(q) for q in a[1].split(",")); A = float(a[2])
F = int(os.environ.get("F", 60)); X0 = float(os.environ.get("X0", -1600))
for n in [o.name for o in bpy.data.objects if o.name.startswith(("lama_stransa_", "balama_lama_", "marcaj_balama_", "eticheta_"))]: bpy.data.objects.remove(bpy.data.objects[n])
for cn in ("LAMA_STARI", "BALAMALE_INCERCATE"):
    c = bpy.data.collections.get(cn)
    if c: bpy.data.collections.remove(c)
sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, 2 * F; sc.render.fps = 30
for sd, sg in (("S", 1), ("D", -1)):
    o = bpy.data.objects["an_lama_" + sd]; Hw = Vector((sg * hx + X0, hy, hz))                       # hinge in world
    Hl = o.matrix_world.inverted() @ Hw; o.data.transform(Matrix.Translation(-Hl)); o.location = Hw; o.rotation_mode = "XYZ"
    o.animation_data_clear()
    for fr, ang in ((1, sg * A), (F, 0.0), (2 * F, sg * A)):
        o.rotation_euler = (0, 0, math.radians(ang)); o.keyframe_insert("rotation_euler", index=2, frame=fr)
    for fc in o.animation_data.action.fcurves:
        for k in fc.keyframe_points: k.interpolation = "BEZIER"; k.handle_left_type = k.handle_right_type = "AUTO_CLAMPED"
    print("ANIM %s: origine pe balama %s, cadru 1 strans (%+.1f), cadru %d deschis, cadru %d strans" % (o.name, tuple(round(v, 1) for v in Hw), sg * A, F, 2 * F))
sc.frame_set(F); bpy.ops.wm.save_as_mainfile(filepath=OUT)
