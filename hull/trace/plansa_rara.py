# The board cleaned and spread out (asked: keep only the model, the assembled guides, the new ship and the workshop copy with the
# sliding doors and the animation, a bit more room between them along X to orbit the camera freely): every other collection removed
# with its objects, the kept blocks moved along X by the given offsets (top-level objects; animated locations shifted with their
# keys), the D halves of the welded guides that had been mirrored about x = 0 put back as the mirror of S about the guides' centre
# (MIRFIX names, offset -2 * centre), unused data purged.
# Usage: blender -b <f.blend> --python plansa_rara.py -- <out.blend> COLECTIE=dx ...   env MIRFIX=g_as_bf_sudat_D,g_as_nac_sudat_D MIRC=-3100
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; DX = {k: float(v) for k, v in (t.split("=") for t in a[1:])}
keep = {o for c in bpy.data.collections if c.name in DX for o in c.all_objects}
for c in list(bpy.data.collections):
    if c.name in DX: continue
    for o in list(c.objects):
        if o not in keep: bpy.data.objects.remove(o)
    bpy.data.collections.remove(c)
mc = float(os.environ.get("MIRC", -3100))
for n in [t for t in os.environ.get("MIRFIX", "g_as_bf_sudat_D,g_as_nac_sudat_D").split(",") if t]:
    o = bpy.data.objects.get(n)
    if o: o.location.x += 2 * mc; print("PLANSA %s: oglinda lui S fata de x %.0f (mutat %.0f)" % (n, mc, 2 * mc))
def shift(o, dx):
    o.location.x += dx; ad = o.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            if fc.data_path == "location" and fc.array_index == 0:
                for kp in fc.keyframe_points: kp.co[1] += dx; kp.handle_left[1] += dx; kp.handle_right[1] += dx
for cn, dx in DX.items():
    if not dx: continue
    obs = [o for o in bpy.data.collections[cn].all_objects if o.parent is None]
    for o in obs: shift(o, dx)
    print("PLANSA %s: %d obiecte mutate %.0f m pe X" % (cn, len(obs), dx))
bpy.ops.outliner.orphans_purge(do_recursive=True); bpy.context.scene.frame_set(1); bpy.ops.wm.save_as_mainfile(filepath=OUT)
