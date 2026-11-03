# The blade piece (asked: draw the surface): the ship grey, an_lama_S/D red; the separate copy with its guides; from above, oblique
# front, from the side, close at the root and along the middle. Usage: blender -b <f.blend> --python render_lama.py -- <out_prefix>
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
nava = set(bpy.data.collections["ASAMBLAT_NOU"].objects); sep = set(bpy.data.collections["GHIDAJ_LAMA_SEPARAT"].objects)
for o in nava: o.color = (.72, .72, .75, 1)
for n in ("an_lama_S", "an_lama_D", "lama_separat_S"): bpy.data.objects[n].color = (.85, .08, .08, 1)
for o in sep:
    if o.type == "CURVE": o.color = (1, .85, .1, 1) if o.name.startswith("g_lamasep_") else (.35, .55, 1, 1); o.data.bevel_depth = .8
sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 40
views = (("separat_oblic", sep, Vector((-5200 - 300, 450, 150)), (-.6, .8, .6), 1000), ("separat_aproape", sep, Vector((-5200 - 380, 560, 150)), (-.9, .4, .3), 380),
         ("nava_sus", nava, Vector((-1600, 420, 200)), (0, -.05, 1), 1500), ("nava_oblic", nava, Vector((-1600 - 150, 450, 200)), (-.5, 1, .6), 1300),
         ("nava_lateral", nava, Vector((-1600 - 300, 420, 200)), (-1, .1, .2), 1000), ("nava_radacina", nava, Vector((-1600 - 120, 260, 285)), (-.4, -.7, .6), 330))
for n, objs, c, d, R in views:
    for o in sc.objects: o.hide_render = o not in objs
    co.location = c + Vector(d).normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = "%s_%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)
