# The four small ear tabs under the PS frame pulled off the surfaces they coincided with (asked: finish the decorations; their
# underside z 275 lay exactly on the PS frame's underside - the two fought in renders - and their top z 280 on PS's underside):
# each tab's z stretched about its own range so the underside goes DOWN m lower and the top UP m into PS; x, y untouched.
# Usage: blender -b <in.blend> --python urechiuse_fara_suprapunere.py -- <out.blend> ; env DOWN=0.3 UP=0.2
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; DOWN, UP = float(os.environ.get("DOWN", .3)), float(os.environ.get("UP", .2))
for n in ("an_urechiusa_1_S", "an_urechiusa_2_S", "an_urechiusa_1_D", "an_urechiusa_2_D"):
    me = bpy.data.objects[n].data; zs = [v.co.z for v in me.vertices]; z0, z1 = min(zs), max(zs)
    for v in me.vertices: v.co.z = (z0 - DOWN) + (v.co.z - z0) * ((z1 + UP) - (z0 - DOWN)) / (z1 - z0)
    me.update(); print("URECHIUSA %s: z %.2f..%.2f -> %.2f..%.2f" % (n, z0, z1, z0 - DOWN, z1 + UP))
bpy.ops.wm.save_as_mainfile(filepath=a[0])
