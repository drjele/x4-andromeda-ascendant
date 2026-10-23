# Deviation map: the original coloured by its distance to our nearest surface (green close, red missing).
import bpy, bmesh, colorsys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath="/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]; bpy.context.window.scene = sc; b = bmesh.new()
for o in sc.objects:
    if o.type == "MESH" and not o.name.startswith("source"): b.from_mesh(o.data)
T = BVHTree.FromBMesh(b)
src = sc.objects["source"]; me = src.data; ca = me.color_attributes.new("dev", "FLOAT_COLOR", "POINT")
for v in me.vertices:
    d = T.find_nearest(v.co)[3] or 999; t = min(1.0, max(0.0, (d - 6) / 30.0)); r, g, bb = colorsys.hsv_to_rgb(0.33 * (1 - t), 0.85, 0.9); ca.data[v.index].color = (r, g, bb, 1)
me.color_attributes.active_color = ca
for o in sc.objects: o.hide_render = o.name != "source"
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "FLAT"; sc.display.shading.color_type = "VERTEX"
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.clip_end = 20000
for v, loc, tgt, res in [("top", (0, 0, 5000), (0, 0, 0), (1100, 1600)), ("bot", (0, 0, -5000), (0, 0, 0), (1100, 1600)), ("side", (5000, 0, 0), (0, 0, 0), (1600, 700)), ("front", (0, 5000, 0), (0, 0, 0), (1300, 700))]:
    sc.render.resolution_x, sc.render.resolution_y = res; cam.data.ortho_scale = 2850 if v != "front" else 1700
    cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/arms/dev_{v}.png"; bpy.ops.render.render(write_still=True)
