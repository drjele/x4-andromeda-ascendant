"""Blender integration checks for extraction, mounting, articulation and muzzle placement.

Run with -- <ship.blend> <turret.blend> after exporting both scenes.
"""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import andromeda_import as hull
import andromeda_turrets as turret

hull.clear_scene()
source = hull.import_source()
hull.repair_winding(source)
found = turret.assemblies(source.data)
canonical, canonical_pivot, canonical_frame = found[1]
# All four models must be congruent, including their original hull-fitting sockets.
for parts, pivot, frame in found:
    for indices, _, _ in parts:
        reference = [
            canonical_frame.transposed() @ (source.data.vertices[i].co - canonical_pivot)
            for other, _, _ in canonical
            if len(other) == len(indices)
            for i in other
        ]
        for i in indices:
            point = frame.transposed() @ (source.data.vertices[i].co - pivot)
            assert min((point - p).length for p in reference) < 0.001
original_faces = len(source.data.polygons)
original_bounds = [
    (min(v.co[a] for v in source.data.vertices), max(v.co[a] for v in source.data.vertices))
    for a in range(3)
]
positions = turret.remove_from_hull(source)
assert original_faces - len(source.data.polygons) == 1016
assert [
    (min(v.co[a] for v in source.data.vertices), max(v.co[a] for v in source.data.vertices))
    for a in range(3)
] == original_bounds
factor, center = hull.normalize(source)
print(
    "Four congruent original turrets separated; hull bounds retained; no duplicate static barrels"
)
ship_file, turret_file = map(Path, sys.argv[sys.argv.index("--") + 1 :])
bpy.ops.wm.open_mainfile(filepath=str(ship_file))
for index, (pivot, frame) in enumerate(positions, 1):
    mount = bpy.data.objects[f"con_turret_integrated_{index:02d}"]
    assert (mount.location - (pivot - center) * factor).length < 0.001
    for axis in range(3):
        assert (mount.rotation_euler.to_matrix().col[axis] - frame.col[axis]).length < 0.001
bpy.ops.wm.open_mainfile(filepath=str(turret_file))
parts = {name: bpy.data.objects[name] for name in ("part_socket", "part_yaw", "part_pitch")}
assert parts["part_yaw"].parent == parts["part_socket"]
assert parts["part_pitch"].parent == parts["part_yaw"]
for part in parts.values():
    for polygon in part.data.polygons:
        normal = sum((part.data.corner_normals[i].vector for i in polygon.loop_indices), Vector())
        assert polygon.normal.dot(normal) > 0
barrel_tip = max(v.co.y for v in parts["part_pitch"].data.vertices)
for i in (1, 2):
    muzzle = bpy.data.objects[f"con_laser_{i:02d}"]
    assert muzzle.parent == parts["part_pitch"]
    assert 0 < muzzle.location.y - barrel_tip < 1
    rest = muzzle.matrix_world.translation.copy()
    parts["part_yaw"].rotation_euler.z = math.radians(60)
    parts["part_pitch"].rotation_euler.x = math.radians(30)
    bpy.context.view_layer.update()
    assert (muzzle.matrix_world.translation - rest).length > 20
    assert (muzzle.matrix_world.to_quaternion() @ Vector((0, 1, 0))).z > 0.4
    parts["part_yaw"].rotation_euler.z = 0
    parts["part_pitch"].rotation_euler.x = 0
    bpy.context.view_layer.update()
print("Original mount transforms, coherent normals, moving barrels and muzzle clearance passed")
