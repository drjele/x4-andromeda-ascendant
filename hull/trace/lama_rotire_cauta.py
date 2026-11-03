# Where to hinge the blade and how far to turn it to stow it (asked: an_lama_S is the one; its hinge / turning point further back
# than now): for each candidate pivot (x, y on the blade's root line, z of the root) and each angle about the vertical axis (both
# senses), the blade copy turned and rendered small with the ship (blade pure red, ship grey) from above, below and oblique; the red
# pixels left, as a share of the open blade's. Prints the table and the best angle per pivot.
# OBJ=<object> (default an_lama_S): which blade piece is turned (the others named an_lama* are hidden).
# A pivot given as x:y (e.g. 0:-40) instead of a bare y sets its x too (default x -59.6). Also prints where the root centre lands.
# Usage: blender -b <f.blend> --python lama_rotire_cauta.py -- <y1,x:y,...> <angles deg, e.g. -90:90:10> ; env RES=360
# NOTE 2026-11-02: before the Standard view transform the red count was wrong (the colour transform pushed it under the threshold);
# results from before that are not to be trusted - lama_ascuns_raze.py (rays) is the reliable check.
import bpy, sys, os, numpy as np, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; YS = [tuple(float(x) for x in q.split(":")) if ":" in q else (-59.6, float(q)) for q in a[0].split(",")]; A0, A1, AS = (float(q) for q in a[1].split(":"))
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "FLAT"; sc.view_settings.view_transform = "Standard"; sh.color_type = "OBJECT"; sh.show_cavity = False
sh.show_shadows = False; sh.show_specular_highlight = False
res = int(os.environ.get("RES", 360)); sc.render.resolution_x, sc.render.resolution_y = res, int(res * .75); sc.render.image_settings.file_format = "PNG"
blade = bpy.data.objects[os.environ.get("OBJ", "an_lama_S")]; ship = [o for o in bpy.data.collections["ASAMBLAT_NOU"].objects if not o.name.startswith("an_lama")]
for o in sc.objects: o.hide_render = not (o in ship or o is blade)
for o in ship: o.color = (.5, .5, .5, 1)
blade.color = (1, 0, 0, 1); M0 = blade.matrix_world.copy()
root = np.array([v.co[:] for v in blade.data.vertices]); r0 = root[np.argmin(root[:, 1] * 0 + np.abs(root[:, 0] + 59.6))]   # a root point (x -59.6)
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 35
c = Vector((-1600 - 250, 420, 200)); views = [(0, -.05, 1), (0, -.05, -1), (-.5, 1, .55), (-.5, .8, -.6)]
tmp = "/tmp/claude-1000/-home-adrian-projects-drjele-x4-andromeda-ascendant/ceeedc00-3e89-4f76-a893-e69366c1beee/scratchpad/rot.png"
def red():
    tot = 0
    for d in views:
        co.location = c + Vector(d).normalized() * 1300; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = tmp; bpy.ops.render.render(write_still=True); im = bpy.data.images.load(tmp); px = np.array(im.pixels[:]).reshape(-1, 4)
        tot += int(((px[:, 0] > .8) & (px[:, 1] < .2) & (px[:, 2] < .2)).sum()); bpy.data.images.remove(im)
    return tot
base = red(); print("ROT lama deschisa: %d pixeli rosii (4 vederi)" % base)
R0 = Vector((-59.6, 262.4, 0))
for px, y in YS:
    P = Vector((px - 1600, y, float(os.environ.get('PZ', r0[2]))))
    row = []
    for ang in np.arange(A0, A1 + .1, AS):
        R = Matrix.Translation(P) @ Matrix.Rotation(math.radians(ang), 4, "Z") @ Matrix.Translation(-P)
        blade.matrix_world = R @ M0; bpy.context.view_layer.update(); rc = Matrix.Rotation(math.radians(ang), 3, 'Z') @ (R0 - Vector((px, y, 0))) + Vector((px, y, 0)); row.append((ang, red() / base, rc.x, rc.y))
    blade.matrix_world = M0
    best = min(row, key=lambda q: q[1])
    print("ROT pivot (%.0f, %.0f): " % (px, y) + "  ".join("%+.0f:%.2f" % q[:2] for q in row)); print("ROT    cel mai bun: %+.0f grade, se mai vede %.1f%%, radacina la (%.1f, %.1f)" % (best[0], 100 * best[1], best[2], best[3]))
