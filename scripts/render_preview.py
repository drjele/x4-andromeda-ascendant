"""Render six orthographic Workbench views of a saved scene for visual review.

Run with -- <scene.blend> <output directory>. The scene file is not modified.
"""

import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

VIEWS = {
    "front": Vector((0, 1, 0)),
    "back": Vector((0, -1, 0)),
    "left": Vector((-1, 0, 0)),
    "right": Vector((1, 0, 0)),
    "top": Vector((0, 0, 1)),
    "bottom": Vector((0, 0, -1)),
}

scene_file, output = map(Path, sys.argv[sys.argv.index("--") + 1 :])
bpy.ops.wm.open_mainfile(filepath=str(scene_file))
scene = bpy.context.scene
meshes = [o for o in scene.objects if o.type == "MESH" and o.visible_get()]
assert meshes, "no visible meshes"
corners = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
low = Vector(min(c[a] for c in corners) for a in range(3))
high = Vector(max(c[a] for c in corners) for a in range(3))
center = (low + high) / 2
size = (high - low).length

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_cavity = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects.new("preview_camera", bpy.data.cameras.new("preview_camera"))
scene.collection.objects.link(camera)
camera.data.type = "ORTHO"
camera.data.ortho_scale = size * scene.render.resolution_x / scene.render.resolution_y
camera.data.clip_end = size * 4
scene.camera = camera

output.mkdir(parents=True, exist_ok=True)
for name, direction in VIEWS.items():
    camera.location = center + direction * size * 2
    up = Vector((0, 1, 0)) if abs(direction.z) == 1 else Vector((0, 0, 1))
    right = up.cross(direction)
    camera.rotation_euler = (
        Matrix((right, direction.cross(right), direction)).transposed().to_euler()
    )
    scene.render.filepath = str(output / f"{scene_file.stem}_{name}.png")
    bpy.ops.render.render(write_still=True)
print(f"Rendered {len(VIEWS)} views to {output}")
