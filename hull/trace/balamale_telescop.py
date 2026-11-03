# Telescopic hinges (asked: the hinges at_spinare_* keep their contact point in the arm fixed, where it is when the blades are
# stowed, and grow longer like a telescope - opened they floated in the air): the column (unit cylinder, origin on its top, length
# = scale z) keeps its top at the stowed top for the whole animation; at every key the bottom stays where it was (top - length
# before, sampled every frame) and the length becomes stowed top - that bottom (baked per frame, linear). Open / stowed workshop copies (d_ / s_) the same, static.
# Usage: blender -b <scene> --python balamale_telescop.py -- <out.blend>
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
for o in [x for x in bpy.data.objects if x.name.startswith(("at_spinare_", "d_spinare_", "s_spinare_"))]:
    ad = o.animation_data; act = ad.action if ad else None
    if not act:                                                           # static copies: stowed top from the at_ twin's first key
        tw = bpy.data.objects.get("at_" + o.name.split("_", 1)[1]); fz = tw.animation_data.action.fcurves.find("location", index=2)
        top = fz.keyframe_points[0].co[1]; bot = o.location.z - o.scale.z; o.location.z = top; o.scale.z = top - bot
        print("TELESCOP %s: varf %.1f, jos %.1f, lungime %.1f m" % (o.name, top, bot, top - bot)); continue
    fz = act.fcurves.find("location", index=2); fs = act.fcurves.find("scale", index=2); top = fz.keyframe_points[0].co[1]
    F = range(sc.frame_start, sc.frame_end + 1); bot = [fz.evaluate(f) - fs.evaluate(f) for f in F]   # bottom of the old column, every frame
    for kp in list(fz.keyframe_points)[1:]: fz.keyframe_points.remove(fz.keyframe_points[1])
    fz.keyframe_points[0].co[1] = top; fz.update()
    while len(fs.keyframe_points): fs.keyframe_points.remove(fs.keyframe_points[0])
    fs.keyframe_points.add(len(F))
    for kp, f, b in zip(fs.keyframe_points, F, bot): kp.co = (f, top - b); kp.interpolation = "LINEAR"
    fs.update()
    print("TELESCOP %s: varf fix %.1f, lungime %.1f (strans) .. %.1f m (deschis), copt pe %d cadre" % (o.name, top, top - max(bot), top - min(bot), len(F)))
sc.frame_set(1); bpy.ops.wm.save_as_mainfile(filepath=OUT)
