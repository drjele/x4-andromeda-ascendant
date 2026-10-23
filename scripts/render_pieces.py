"""Render a review sheet for each hull piece and one of all pieces together.

Run with -- <ship_pieces.blend> <output directory>. Each piece is drawn alone in its colour, from
above, the side, ahead and three-quarters, at the scale of the whole ship.
"""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

VIEWS = {
    "top": ((0, 0, 6000), (0, 0, 0)),
    "side": ((6000, 0, 0), (0, 0, 0)),
    "front": ((0, 6000, 0), (0, 0, 0)),
    "quarter": ((3600, 3000, 2400), (0, 0, 0)),
}
SIZE = (900, 700)

source, output = map(Path, sys.argv[sys.argv.index("--") + 1 :])
output.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(source))
scene = bpy.data.scenes["pieces"]
bpy.context.window.scene = scene
pieces = [o for o in scene.objects if o.type == "MESH"]
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.render.resolution_x, scene.render.resolution_y = SIZE
scene.render.film_transparent = False
camera = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
scene.collection.objects.link(camera)
scene.camera = camera
camera.data.type = "ORTHO"
camera.data.ortho_scale = 3000
camera.data.clip_end = 20000


def render(name, focus):
    for piece in pieces:
        piece.hide_render = focus not in (None, piece)
    for view, (location, target) in VIEWS.items():
        camera.location = location
        camera.rotation_euler = (
            (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()
        )
        if "top" == view:
            camera.rotation_euler = (0.0, 0.0, math.pi / 2)
        scene.render.filepath = str(output / f"{name}_{view}.png")
        bpy.ops.render.render(write_still=True)


render("all", None)
for piece in pieces:
    render(piece.name, piece)
print(f"rendered {len(pieces)} pieces to {output}")
