# Close-up render of a region (asked: black streaks on at_PS_carena / the compartments towards it, at_usa_fata_D outline): ortho
# camera from the given direction, centred on a ship point (atelier x offset added), given width; workbench studio light, cavity,
# outline, object colours (hatch blue, blades yellow, columns red, hull grey), backface culling optional (CULL=1).
# Usage: blender -b <scene> --python render_zona.py -- <out.png> <x,y,z ship> <width> <dir: jos|sus|oblic|x+|x-> <frame>
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, C, W, D, FR = a[0], Vector([float(t) for t in a[1].split(",")]), float(a[2]), a[3], int(a[4])
C.x += float(os.environ.get("XOFF", -7000)); sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True
sh.show_object_outline = True; sh.color_type = os.environ.get("CT", "OBJECT"); sh.show_backface_culling = bool(int(os.environ.get("CULL", 0)))
col = set(o for c in os.environ.get("COL", "ATELIER_LAME").split(",") for o in bpy.data.collections[c].objects)
for o in sc.objects: o.hide_render = o not in col
for o in col:
    if o.type == "CURVE": continue
    o.color = (1, .85, 0, 1) if "_lama_" in o.name else (.85, .08, .08, 1) if "spinare" in o.name else (.1, .5, 1, 1) if "_usa_" in o.name else (.72, .72, .75, 1)
sc.frame_set(FR); sc.render.resolution_x = sc.render.resolution_y = 1400
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.type = "ORTHO"; cam.ortho_scale = W
dv = {"jos": Vector((0, 0, -1)), "sus": Vector((0, 0, 1)), "oblic": Vector((.5, -.5, -.7)).normalized(), "x+": Vector((1, 0, 0)), "x-": Vector((-1, 0, 0)), "oblicD": Vector((-.5, -.5, -.7)).normalized()}[D]
co.location = C + dv * 3000; co.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler(); sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
