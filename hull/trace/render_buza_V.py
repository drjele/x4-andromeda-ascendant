# Close-up of the front arm at the V of its lip (asked: see the V zone before changing it): the arm grey, its lip guide
# (taken out of the welded body, moved onto the arm) red, from below (-Z), above and oblique, centred on a ship-space point.
# Usage: blender -b <f.blend> --python render_buza_V.py -- <out_prefix> <piece> <welded guide> <guide name> <x,y,z ship> [R=120]
import bpy, sys, json
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, PIECE, WG, GN = a[:4]; C = Vector([float(q) for q in a[4].split(",")])
R = float(a[5]) if len(a) > 5 else 120; X0, GX = 1600, 3100; sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
for o in sc.objects: o.hide_render = o.name != PIECE
p = bpy.data.objects[PIECE]; p.color = (.75, .75, .78, 1)
gc = bpy.data.objects[WG]; sp = gc.data.splines[json.loads(gc["linii"]).index(GN)]
cu = bpy.data.curves.new("buza", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.5; s2 = cu.splines.new("POLY"); s2.points.add(len(sp.points) - 1)
for q, pt in zip(s2.points, sp.points): q.co = (*(gc.matrix_world @ pt.co.xyz + Vector((GX - X0, 0, 0))), 1)
go = bpy.data.objects.new("buza", cu); sc.collection.objects.link(go); go.color = (1, .1, .1, 1)
c = C - Vector((X0, 0, 0)); sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.lens = 50; cam.clip_end = 20000
for n, d in (("jos", (0, -.2, -1)), ("sus", (0, -.2, 1)), ("oblic", (.7, -.6, -.5))):
    d = Vector(d).normalized(); co.location = c + d * R * 2.2; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = "%s_%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)
