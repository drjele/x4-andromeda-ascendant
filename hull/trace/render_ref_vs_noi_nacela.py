# Reference nacelles vs ours (asked: "look at the reference nacelles, at what angles they are"): the same views on the reference
# ship (x 0, its nacelle ribs R1xx/R2xx red, Circle.007 yellow) and on our copy (x -1600, nacelles red, blade an_lama deployed yellow
# at frame F); oblique front, from the side along the arm and from the front-inside. Usage: ... -- <out_prefix> [F=60]
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; F = int(a[1]) if len(a) > 1 else 60
sc = bpy.context.scene; sc.frame_set(F); sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
ref = set(bpy.data.collections["REFERINTA"].all_objects); our = set(bpy.data.collections["ASAMBLAT_NOU"].objects)
def is_rib(o):
    if not (o.name.startswith("R") and " 0" in o.name) or o.type != "MESH" or len(o.data.vertices) > 200: return False
    c = sum((o.matrix_world @ v.co for v in o.data.vertices), Vector()) / len(o.data.vertices); return -560 < abs(c.x) * -1 < -100 and 150 < c.y < 620 and 80 < c.z < 320
for o in ref: o.color = (1, .85, 0, 1) if o.name.startswith("Circle.007") else (.85, .1, .1, 1) if is_rib(o) else (.72, .72, .75, 1)
for o in our: o.color = (1, .85, 0, 1) if o.name.startswith("an_lama") else (.45, .04, .04, 1) if "nacela_inchis" in o.name else (.9, .4, .4, 1) if "nacela_deschis" in o.name else (.72, .72, .75, 1)
sc.render.resolution_x, sc.render.resolution_y = 900, 700
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 40
for blk, objs, x0 in (("referinta", ref, 0), ("noi", our, -1600)):
    for o in sc.objects: o.hide_render = o not in objs or (blk == "referinta" and o.name.startswith("Circle") and o.name != "Circle.007")
    c = Vector((x0 - 330, 380, 200))
    for n, d, R in (("oblic", (-.5, 1, .55), 1000), ("lateral", (-1, .15, .1), 900), ("din_interior", (.6, .9, .25), 800)):
        co.location = c + Vector(d).normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = "%s_%s_%s.png" % (OUT, blk, n); bpy.ops.render.render(write_still=True)
