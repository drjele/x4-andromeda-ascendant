# Hinge 7 + slide (asked: the blade is not shortened; check if the nacelle hides the rest, else turn + slide): the blade turned ANG
# about the vertical through the pivot, then slid D m along SLIDE (default: minus the blade's mean across direction, i.e. towards the
# arm); pixels of the blade left (above, below, two obliques, the root close up above and below) as a share of the open blade's.
# Usage: blender -b <f.blend> --python lama_rotire_alunecare.py -- <px,py,pz> <angles a0:a1:s> <slides d0:d1:s> ; env SLIDE=x,y,z RES=1000
# NOTE 2026-11-02: before the Standard view transform the red count was wrong (the colour transform pushed it under the threshold);
# results from before that are not to be trusted - lama_ascuns_raze.py (rays) is the reliable check.
import bpy, sys, os, numpy as np, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; px, py, pz = (float(q) for q in a[0].split(","))
rng = lambda s: np.arange(*(lambda t: (t[0], t[1] + 1e-6, t[2]))([float(q) for q in s.split(":")])); ANGS, DS = rng(a[1]), rng(a[2])
if os.environ.get("SLIDE"): sv = np.array([float(q) for q in os.environ["SLIDE"].split(",")])
else: U = np.load("/home/adrian/Documents/Andromeda/2026-10-29-imbinari/piese/ghid_lama_v6_param.npz")["U"]; sv = -U.mean(0)
sv = sv / np.linalg.norm(sv); print("ALUN directia de alunecare", sv.round(3))
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "FLAT"; sc.view_settings.view_transform = "Standard"; sh.color_type = "OBJECT"; sh.show_cavity = False
res = int(os.environ.get("RES", 1000)); sc.render.resolution_x, sc.render.resolution_y = res, int(res * .75)
blade = bpy.data.objects["an_lama_S"]; ship = [o for o in bpy.data.collections["ASAMBLAT_NOU"].objects if not o.name.startswith("an_lama")]
for o in sc.objects: o.hide_render = not (o in ship or o is blade)
for o in ship: o.color = (.5, .5, .5, 1)
blade.color = (1, 0, 0, 1); M0 = blade.matrix_world.copy(); P = Vector((px - 1600, py, pz))
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 35
c = Vector((-1800, 380, 220)); views = [(c, (0, -.05, 1), 1000), (c, (0, -.05, -1), 1000), (c, (-.5, 1, .55), 900), (c, (-.5, .8, -.6), 900),
         (Vector((-1700, 200, 285)), (-.3, -.5, 1), 330), (Vector((-1700, 200, 280)), (-.3, .3, -1), 330)]          # + the root close up (above / below)
tmp = "/tmp/claude-1000/-home-adrian-projects-drjele-x4-andromeda-ascendant/ceeedc00-3e89-4f76-a893-e69366c1beee/scratchpad/ra.png"
def red():
    tot = 0
    for cc, d, R in views:
        co.location = cc + Vector(d).normalized() * R; co.rotation_euler = (cc - co.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = tmp; bpy.ops.render.render(write_still=True); im = bpy.data.images.load(tmp); q = np.array(im.pixels[:]).reshape(-1, 4)
        tot += int(((q[:, 0] > .8) & (q[:, 1] < .2) & (q[:, 2] < .2)).sum()); bpy.data.images.remove(im)
    return tot
base = red(); best = None
for ang in ANGS:
    row = []
    for d in DS:
        blade.matrix_world = Matrix.Translation(Vector(sv * d)) @ Matrix.Translation(P) @ Matrix.Rotation(math.radians(ang), 4, "Z") @ Matrix.Translation(-P) @ M0
        bpy.context.view_layer.update(); f = red() / base; row.append((d, f))
        if best is None or (f, d) < (best[0], best[2]): best = (f, ang, d)
    print("ALUN rotire %+5.1f: " % ang + "  ".join("%.0f m:%.1f%%" % (q[0], 100 * q[1]) for q in row))
blade.matrix_world = M0; print("ALUN cel mai bun: rotire %+.1f, alunecare %.0f m -> %.1f%%" % (best[1], best[2], 100 * best[0]))
