# Hinge 7 kept, its axis tilted (asked: the hinge at point 7 - the arm's middle by PS - is right; with a vertical axis a root corner
# and the tip stay out): the blade turned ANG about an axis through the pivot tilted TILT deg from vertical towards azimuth AZ; the
# blade's pixels left (above, below, two obliques) as a share of the open blade's. Prints the table and the best.
# Usage: blender -b <f.blend> --python lama_axa_inclinata.py -- <px,py,pz> <angles a0:a1:s> <tilts t0:t1:s> <azimuths deg,...> ; env RES=1000
# NOTE 2026-11-02: before the Standard view transform the red count was wrong (the colour transform pushed it under the threshold);
# results from before that are not to be trusted - lama_ascuns_raze.py (rays) is the reliable check.
import bpy, sys, os, numpy as np, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; px, py, pz = (float(q) for q in a[0].split(","))
rng = lambda s: np.arange(*(lambda t: (t[0], t[1] + 1e-6, t[2]))([float(q) for q in s.split(":")])); ANGS, TILTS = rng(a[1]), rng(a[2]); AZS = [float(q) for q in a[3].split(",")]
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "FLAT"; sc.view_settings.view_transform = "Standard"; sh.color_type = "OBJECT"; sh.show_cavity = False
res = int(os.environ.get("RES", 1000)); sc.render.resolution_x, sc.render.resolution_y = res, int(res * .75)
blade = bpy.data.objects["an_lama_S"]; ship = [o for o in bpy.data.collections["ASAMBLAT_NOU"].objects if not o.name.startswith("an_lama")]
for o in sc.objects: o.hide_render = not (o in ship or o is blade)
for o in ship: o.color = (.5, .5, .5, 1)
blade.color = (1, 0, 0, 1); M0 = blade.matrix_world.copy(); P = Vector((px - 1600, py, pz))
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 35
c = Vector((-1800, 380, 220)); views = [((0, -.05, 1), 1000), ((0, -.05, -1), 1000), ((-.5, 1, .55), 900), ((-.5, .8, -.6), 900)]
tmp = "/tmp/claude-1000/-home-adrian-projects-drjele-x4-andromeda-ascendant/ceeedc00-3e89-4f76-a893-e69366c1beee/scratchpad/ax.png"
def red():
    tot = 0
    for d, R in views:
        co.location = c + Vector(d).normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = tmp; bpy.ops.render.render(write_still=True); im = bpy.data.images.load(tmp); px_ = np.array(im.pixels[:]).reshape(-1, 4)
        tot += int(((px_[:, 0] > .8) & (px_[:, 1] < .2) & (px_[:, 2] < .2)).sum()); bpy.data.images.remove(im)
    return tot
base = red(); best = None
for tl in TILTS:
    for az in (AZS if tl > 0 else [0]):
        ax = Vector((math.sin(math.radians(tl)) * math.cos(math.radians(az)), math.sin(math.radians(tl)) * math.sin(math.radians(az)), math.cos(math.radians(tl))))
        row = []
        for ang in ANGS:
            blade.matrix_world = Matrix.Translation(P) @ Matrix.Rotation(math.radians(ang), 4, ax) @ Matrix.Translation(-P) @ M0; bpy.context.view_layer.update()
            f = red() / base; row.append((ang, f))
            if best is None or f < best[0]: best = (f, tl, az, ang)
        print("AXA inclinata %4.1f spre az %5.0f: " % (tl, az) + "  ".join("%+.0f:%.1f%%" % (q[0], 100 * q[1]) for q in row))
blade.matrix_world = M0
print("AXA cel mai bun: inclinare %.1f spre az %.0f, rotire %+.1f -> se mai vede %.1f%%" % (best[1], best[2], best[3], 100 * best[0]))
