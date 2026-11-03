# Clean lines and surfaces pass (asked: before the blades, one more clean lines / surfaces pass for Adrian to check by eye): one
# piece alone, grey, with its sharp edges drawn over it - dihedral over A1 deg orange, over A2 deg red - from above, below, the
# outer side (orthographic, the whole piece in frame) and oblique. Prints how many edges per class.
# Usage: blender -b <f.blend> --python render_cute.py -- <out_prefix> <piece> [A1=60] [A2=120]
import bpy, sys, bmesh, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, N = a[0], a[1]; A1 = float(a[2]) if len(a) > 2 else 60; A2 = float(a[3]) if len(a) > 3 else 120
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
p = bpy.data.objects[N]
for o in sc.objects: o.hide_render = o is not p
p.color = (.78, .78, .8, 1); mw = p.matrix_world
pts = [mw @ Vector(b) for b in p.bound_box]; lo = Vector([min(q[i] for q in pts) for i in range(3)]); hi = Vector([max(q[i] for q in pts) for i in range(3)])
BEV = max((hi - lo).length * .0012, .3)
bm = bmesh.new(); bm.from_mesh(p.data); cnt = {}
for lim, col, nm in ((A1, (1, .55, 0), "portocaliu"), (A2, (1, 0, 0), "rosu")):
    E = [e for e in bm.edges if len(e.link_faces) == 2 and np.degrees(e.calc_face_angle(0)) > lim and (nm == "rosu" or np.degrees(e.calc_face_angle(0)) <= A2)]
    cnt[nm] = len(E)
    if not E: continue
    cu = bpy.data.curves.new("cute_" + nm, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = BEV
    for e in E:
        s = cu.splines.new("POLY"); s.points.add(1); s.points[0].co = (*(mw @ e.verts[0].co), 1); s.points[1].co = (*(mw @ e.verts[1].co), 1)
    o = bpy.data.objects.new("cute_" + nm, cu); sc.collection.objects.link(o); o.color = (*col, 1)
print("CUTE %s: %d muchii %g..%g grade (portocaliu), %d peste %g (rosu)" % (N, cnt["portocaliu"], A1, A2, cnt["rosu"], A2))
c = (lo + hi) / 2; ext = hi - lo; R = ext.length * 2.5
sc.render.resolution_x, sc.render.resolution_y = 1200, 900
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 40
side = Vector((-1, 0, 0)) if N.endswith("_S") else Vector((1, 0, 0))
for n, d in (("sus", Vector((0, -.03, 1))), ("jos", Vector((0, -.03, -1))), ("lateral", side + Vector((0, -.15, .2))), ("oblic", side + Vector((0, -.8, .9)))):
    co.location = c + d.normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
    if n in ("sus", "jos"): cam.type = "ORTHO"; cam.ortho_scale = max(ext.x, ext.y / .75) * 1.08
    elif n == "lateral": cam.type = "ORTHO"; cam.ortho_scale = max(ext.y, ext.z / .75) * 1.08
    else: cam.type = "PERSP"; cam.lens = 40; co.location = c + d.normalized() * ext.length * 1.6; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = "%s_%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)
