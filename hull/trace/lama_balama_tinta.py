# Hinge from where the stowed root must land (asked: lama_stransa_S's root is too far forward, it should be inside PS level with
# an_urechiusa_2_S): for each turning angle about the vertical, the one pivot that carries the blade's root centre R0 onto the target
# T (both seen from above; z unchanged); the turned blade rendered small with the ship from above, below and two obliques; the
# blade's pixels left as a share of the open blade's. Prints the table and the best angle with its pivot.
# Usage: blender -b <f.blend> --python lama_balama_tinta.py -- <R0x,R0y> <Tx,Ty> <a0:a1:step> ; env RES=1000
# NOTE 2026-11-02: before the Standard view transform the red count was wrong (the colour transform pushed it under the threshold);
# results from before that are not to be trusted - lama_ascuns_raze.py (rays) is the reliable check.
import bpy, sys, os, numpy as np, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; R0 = np.array([float(q) for q in a[0].split(",")]); T = np.array([float(q) for q in a[1].split(",")])
A0, A1, AS = (float(q) for q in a[2].split(":")); X0 = -1600.0
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "FLAT"; sc.view_settings.view_transform = "Standard"; sh.color_type = "OBJECT"; sh.show_cavity = False
res = int(os.environ.get("RES", 1000)); sc.render.resolution_x, sc.render.resolution_y = res, int(res * .75)
blade = bpy.data.objects["an_lama_S"]; ship = [o for o in bpy.data.collections["ASAMBLAT_NOU"].objects if not o.name.startswith("an_lama")]
for o in sc.objects: o.hide_render = not (o in ship or o is blade)
for o in ship: o.color = (.5, .5, .5, 1)
blade.color = (1, 0, 0, 1); M0 = blade.matrix_world.copy()
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 35
c = Vector((X0 - 200, 380, 220)); views = [((0, -.05, 1), 1000), ((0, -.05, -1), 1000), ((-.5, 1, .55), 900), ((-.5, .8, -.6), 900)]
tmp = "/tmp/claude-1000/-home-adrian-projects-drjele-x4-andromeda-ascendant/ceeedc00-3e89-4f76-a893-e69366c1beee/scratchpad/rot.png"
def red():
    tot = 0
    for d, R in views:
        co.location = c + Vector(d).normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = tmp; bpy.ops.render.render(write_still=True); im = bpy.data.images.load(tmp); px = np.array(im.pixels[:]).reshape(-1, 4)
        tot += int(((px[:, 0] > .8) & (px[:, 1] < .2) & (px[:, 2] < .2)).sum()); bpy.data.images.remove(im)
    return tot
def pivot(th):                                                            # rotation by th (deg, CCW from above) taking R0 to T
    m = (R0 + T) / 2; d = T - R0; L = np.linalg.norm(d); nrm = np.array([-d[1], d[0]]) / L
    return m + nrm * (L / 2) / math.tan(math.radians(th) / 2)
base = red(); print("TINTA lama deschisa: %d pixeli" % base); rows = []
for th in np.arange(A0, A1 + .1, AS):
    p = pivot(th); P = Vector((p[0] + X0, p[1], 291.9))
    blade.matrix_world = Matrix.Translation(P) @ Matrix.Rotation(math.radians(th), 4, "Z") @ Matrix.Translation(-P) @ M0; bpy.context.view_layer.update()
    f = red() / base; rows.append((th, p, f)); print("TINTA %+5.1f grade: balama (%.1f, %.1f), se mai vede %.1f%%" % (th, p[0], p[1], 100 * f))
blade.matrix_world = M0
b = min(rows, key=lambda q: q[2]); print("TINTA cel mai bun: %+.1f grade, balama (%.1f, %.1f), %.1f%%" % (b[0], b[1][0], b[1][1], 100 * b[2]))
