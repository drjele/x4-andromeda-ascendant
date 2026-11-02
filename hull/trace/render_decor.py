# Any decoration up close (asked: finish the decorations - check every one for clean lines and a step at the edge): the decoration
# dark, the pieces around it grey; framed on its bounding box from above, oblique from both sides and low along its long side.
# Usage: blender -b <f.blend> --python render_decor.py -- <out_prefix> <decoration object> [margin factor = 1.6]
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, D = a[0], a[1]; K = float(a[2]) if len(a) > 2 else 1.6; sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
d = bpy.data.objects[D]; pts = [d.matrix_world @ Vector(b) for b in d.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)]); c = (lo + hi) / 2; R = max((hi - lo).length * K, 40)
for o in sc.objects:
    near = o.type == "MESH" and o.name.startswith("an_") and all(o.matrix_world @ Vector(b) for b in o.bound_box)
    if near:
        b_ = [o.matrix_world @ Vector(q) for q in o.bound_box]; l2 = Vector([min(p[i] for p in b_) for i in range(3)]); h2 = Vector([max(p[i] for p in b_) for i in range(3)])
        near = all(l2[i] < c[i] + R and h2[i] > c[i] - R for i in range(3))
    o.hide_render = not near
    o.color = (.25, .3, .45, 1) if o == d else (.75, .75, .78, 1)
sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 20000; cam.lens = 50
ax = Vector((1, 0, 0)) if hi.x - lo.x > hi.y - lo.y else Vector((0, 1, 0)); sd = Vector((0, 0, 1)).cross(ax)
for n, dv in (("sus", Vector((0, -.05, 1))), ("oblic_a", sd + Vector((0, 0, .8))), ("oblic_b", -sd + Vector((0, 0, .8))), ("jos_lung", sd * .3 + ax + Vector((0, 0, .25))), ("de_jos", Vector((0, -.05, -1)))):
    co.location = c + dv.normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = "%s_%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)
