"""Procedural Andromeda hull generator for Blender 4.2."""

import bmesh
import bpy
from mathutils import Vector

SHIP_LENGTH = 1300.0
HULL_PROFILE = [
    (0.0, 0.0, 0.0, 0.0),
    (0.04, 0.0066, 0.006, -0.002),
    (0.11, 0.0182, 0.014, -0.004),
    (0.22, 0.0319, 0.023, -0.006),
    (0.35, 0.0468, 0.032, -0.007),
    (0.48, 0.0649, 0.041, -0.008),
    (0.6, 0.0798, 0.047, -0.008),
    (0.7, 0.0836, 0.049, -0.007),
    (0.82, 0.077, 0.047, -0.005),
    (0.92, 0.0649, 0.043, -0.003),
    (1.0, 0.0523, 0.039, 0.0),
]
TOP_EXPONENT = 2.4
BOTTOM_EXPONENT = 3.4
NACELLE_START_T = 0.64
NACELLE_LATERAL = 0.075
NACELLE_HALF_WIDTH = 0.022
NACELLE_HALF_HEIGHT = 0.024
FIN_START_T = 0.56
FIN_END_T = 0.91
FIN_HEIGHT = 0.068
FIN_SWEEP = 0.07
FIN_LATERAL = 0.03
FIN_THICKNESS = 0.006
RING_SEGMENTS = 24
LOD_RING_SEGMENTS = (24, 16, 10, 6)
LOD_PROFILE_STRIDE = (1, 1, 2, 3)
TURRET_ROWS_DORSAL = 4
TURRET_ROWS_VENTRAL = 4
TURRET_SPAN_T = (0.3, 0.88)
COLLECTION_NAME = "andromeda_ascendant"


def clear_previous():
    existing = bpy.data.collections.get(COLLECTION_NAME)
    if None is existing:
        return
    for mesh_object in list(existing.objects):
        bpy.data.objects.remove(mesh_object, do_unlink=True)
    bpy.data.collections.remove(existing)


def make_collection():
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)
    return collection


def superellipse_point(angle_index, segments, half_width, half_height):
    import math

    theta = 2.0 * math.pi * angle_index / segments
    angle_cosine = math.cos(theta)
    angle_sine = math.sin(theta)
    exponent = TOP_EXPONENT if angle_sine >= 0.0 else BOTTOM_EXPONENT
    x = half_width * math.copysign(abs(angle_cosine) ** (2.0 / exponent), angle_cosine)
    z = half_height * math.copysign(abs(angle_sine) ** (2.0 / exponent), angle_sine)
    return (x, z)


def sample_profile(stride):
    if 1 == stride:
        return list(HULL_PROFILE)
    sampled = HULL_PROFILE[::stride]
    if HULL_PROFILE[-1] != sampled[-1]:
        sampled.append(HULL_PROFILE[-1])
    if HULL_PROFILE[0] != sampled[0]:
        sampled.insert(0, HULL_PROFILE[0])
    return sampled


def build_hull_mesh(name, segments, stride):
    profile = sample_profile(stride)
    mesh = bpy.data.meshes.new(name)
    mesh_builder = bmesh.new()
    rings = []
    for position_factor, half_width, half_height, offset in profile:
        y = (0.5 - position_factor) * SHIP_LENGTH
        z_center = offset * SHIP_LENGTH
        if 0.0 == half_width and 0.0 == half_height:
            rings.append([mesh_builder.verts.new((0.0, y, z_center))])
            continue
        ring = []
        for segment_index in range(segments):
            x, z = superellipse_point(segment_index, segments, half_width, half_height)
            ring.append(mesh_builder.verts.new((x * SHIP_LENGTH, y, z_center + z * SHIP_LENGTH)))
        rings.append(ring)
    mesh_builder.verts.ensure_lookup_table()
    for index in range(len(rings) - 1):
        current = rings[index]
        following = rings[index + 1]
        if 1 == len(current):
            apex = current[0]
            for segment_index in range(segments):
                mesh_builder.faces.new(
                    (apex, following[segment_index], following[(segment_index + 1) % segments])
                )
            continue
        for segment_index in range(segments):
            next_segment_index = (segment_index + 1) % segments
            mesh_builder.faces.new(
                (
                    current[segment_index],
                    current[next_segment_index],
                    following[next_segment_index],
                    following[segment_index],
                )
            )
    stern = rings[-1]
    mesh_builder.faces.new(tuple(reversed(stern)))
    bmesh.ops.recalc_face_normals(mesh_builder, faces=mesh_builder.faces)
    mesh_builder.to_mesh(mesh)
    mesh_builder.free()
    return mesh


def build_nacelle_mesh(name, side, segments):
    mesh = bpy.data.meshes.new(name)
    mesh_builder = bmesh.new()
    stations = [
        (NACELLE_START_T, 0.3, 0.35),
        (0.72, 0.8, 0.85),
        (0.85, 1.0, 1.0),
        (0.96, 0.95, 0.95),
        (1.0, 0.8, 0.8),
    ]
    rings = []
    for position_factor, width_scale, height_scale in stations:
        y = (0.5 - position_factor) * SHIP_LENGTH
        x_center = side * NACELLE_LATERAL * SHIP_LENGTH
        ring = []
        for segment_index in range(segments):
            x, z = superellipse_point(
                segment_index,
                segments,
                NACELLE_HALF_WIDTH * width_scale,
                NACELLE_HALF_HEIGHT * height_scale,
            )
            ring.append(mesh_builder.verts.new((x_center + x * SHIP_LENGTH, y, z * SHIP_LENGTH)))
        rings.append(ring)
    mesh_builder.verts.ensure_lookup_table()
    for index in range(len(rings) - 1):
        current = rings[index]
        following = rings[index + 1]
        for segment_index in range(segments):
            next_segment_index = (segment_index + 1) % segments
            mesh_builder.faces.new(
                (
                    current[segment_index],
                    current[next_segment_index],
                    following[next_segment_index],
                    following[segment_index],
                )
            )
    mesh_builder.faces.new(tuple(rings[0]))
    mesh_builder.faces.new(tuple(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(mesh_builder, faces=mesh_builder.faces)
    mesh_builder.to_mesh(mesh)
    mesh_builder.free()
    return mesh


def build_fin_mesh(name, side):
    mesh = bpy.data.meshes.new(name)
    mesh_builder = bmesh.new()
    root_front_y = (0.5 - FIN_START_T) * SHIP_LENGTH
    root_rear_y = (0.5 - FIN_END_T) * SHIP_LENGTH
    tip_front_y = root_front_y - FIN_SWEEP * SHIP_LENGTH
    tip_rear_y = root_rear_y - FIN_SWEEP * 0.4 * SHIP_LENGTH
    x_root = side * FIN_LATERAL * SHIP_LENGTH
    x_tip = side * FIN_LATERAL * 0.55 * SHIP_LENGTH
    z_root = 0.03 * SHIP_LENGTH
    z_tip = FIN_HEIGHT * SHIP_LENGTH
    half = FIN_THICKNESS * 0.5 * SHIP_LENGTH
    outline = [
        (x_root, root_front_y, z_root),
        (x_root, root_rear_y, z_root),
        (x_tip, tip_rear_y, z_tip),
        (x_tip, tip_front_y, z_tip),
    ]
    near = [mesh_builder.verts.new((x - half * side, y, z)) for x, y, z in outline]
    far = [mesh_builder.verts.new((x + half * side, y, z)) for x, y, z in outline]
    mesh_builder.verts.ensure_lookup_table()
    mesh_builder.faces.new(near)
    mesh_builder.faces.new(tuple(reversed(far)))
    for segment_index in range(4):
        next_segment_index = (segment_index + 1) % 4
        mesh_builder.faces.new(
            (
                near[segment_index],
                near[next_segment_index],
                far[next_segment_index],
                far[segment_index],
            )
        )
    bmesh.ops.recalc_face_normals(mesh_builder, faces=mesh_builder.faces)
    mesh_builder.to_mesh(mesh)
    mesh_builder.free()
    return mesh


def new_object(collection, name, mesh):
    mesh_object = bpy.data.objects.new(name, mesh)
    collection.objects.link(mesh_object)
    return mesh_object


def join_into_lod(collection, lod_index):
    segments = LOD_RING_SEGMENTS[lod_index]
    stride = LOD_PROFILE_STRIDE[lod_index]
    suffix = f"_lod{lod_index}"
    parts = [
        new_object(collection, f"hull{suffix}", build_hull_mesh(f"hull{suffix}", segments, stride)),
        new_object(
            collection, f"nacelle_l{suffix}", build_nacelle_mesh(f"nacelle_l{suffix}", -1, segments)
        ),
        new_object(
            collection, f"nacelle_r{suffix}", build_nacelle_mesh(f"nacelle_r{suffix}", 1, segments)
        ),
    ]
    if lod_index < 2:
        parts.append(new_object(collection, f"fin_l{suffix}", build_fin_mesh(f"fin_l{suffix}", -1)))
        parts.append(new_object(collection, f"fin_r{suffix}", build_fin_mesh(f"fin_r{suffix}", 1)))
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    merged = bpy.context.view_layer.objects.active
    merged.name = f"andromeda{suffix}"
    merged.data.name = f"andromeda{suffix}"
    return merged


def build_collision(collection, source):
    mesh = source.data.copy()
    mesh_object = new_object(collection, "andromeda_collision", mesh)
    mesh_builder = bmesh.new()
    mesh_builder.from_mesh(mesh)
    bmesh.ops.convex_hull(mesh_builder, input=mesh_builder.verts, use_existing_faces=True)
    mesh_builder.to_mesh(mesh)
    mesh_builder.free()
    modifier = mesh_object.modifiers.new(name="decimate", type="DECIMATE")
    modifier.ratio = 0.4
    return mesh_object


def hull_half_height_at(position_factor):
    for index in range(len(HULL_PROFILE) - 1):
        start_position, _, start_height, start_offset = HULL_PROFILE[index]
        end_position, _, end_height, end_offset = HULL_PROFILE[index + 1]
        if start_position <= position_factor <= end_position:
            span = end_position - start_position
            factor = 0.0 if 0.0 == span else (position_factor - start_position) / span
            return (
                start_height + (end_height - start_height) * factor,
                start_offset + (end_offset - start_offset) * factor,
            )
    return (HULL_PROFILE[-1][2], HULL_PROFILE[-1][3])


def place_empty(collection, name, location, size):
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "ARROWS"
    empty.empty_display_size = size
    empty.location = Vector(location)
    collection.objects.link(empty)
    return empty


def build_connections(collection):
    display = SHIP_LENGTH * 0.02
    stern_y = -0.5 * SHIP_LENGTH
    for side, label in ((-1, "01"), (1, "02")):
        place_empty(
            collection,
            f"con_engine_{label}",
            (side * NACELLE_LATERAL * SHIP_LENGTH, stern_y, 0.0),
            display,
        )
    start_t, end_t = TURRET_SPAN_T
    for row in range(TURRET_ROWS_DORSAL):
        position_factor = start_t + (end_t - start_t) * row / max(1, TURRET_ROWS_DORSAL - 1)
        half_height, offset = hull_half_height_at(position_factor)
        y = (0.5 - position_factor) * SHIP_LENGTH
        z = (offset + half_height) * SHIP_LENGTH
        place_empty(collection, f"con_turret_{row * 2 + 1:03d}", (0.0, y, z), display)
    for row in range(TURRET_ROWS_VENTRAL):
        position_factor = start_t + (end_t - start_t) * row / max(1, TURRET_ROWS_VENTRAL - 1)
        half_height, offset = hull_half_height_at(position_factor)
        y = (0.5 - position_factor) * SHIP_LENGTH
        z = (offset - half_height) * SHIP_LENGTH
        place_empty(collection, f"con_turret_{row * 2 + 2:03d}", (0.0, y, z), display)
    for index, position_factor in enumerate((0.4, 0.56, 0.72, 0.86)):
        half_height, offset = hull_half_height_at(position_factor)
        y = (0.5 - position_factor) * SHIP_LENGTH
        place_empty(
            collection, f"con_shield_{index + 1:02d}", (0.0, y, offset * SHIP_LENGTH), display
        )
    half_height, offset = hull_half_height_at(0.66)
    place_empty(
        collection,
        "con_dock_01",
        (0.0, (0.5 - 0.66) * SHIP_LENGTH, (offset - half_height) * SHIP_LENGTH),
        display * 2.0,
    )
    half_height, offset = hull_half_height_at(0.18)
    place_empty(
        collection,
        "con_cockpit",
        (0.0, (0.5 - 0.18) * SHIP_LENGTH, (offset + half_height * 0.6) * SHIP_LENGTH),
        display,
    )


def main():
    clear_previous()
    collection = make_collection()
    highest_detail_object = None
    for lod_index in range(len(LOD_RING_SEGMENTS)):
        merged = join_into_lod(collection, lod_index)
        if 0 == lod_index:
            highest_detail_object = merged
    build_collision(collection, highest_detail_object)
    build_connections(collection)
    print(
        f"andromeda: {SHIP_LENGTH:.0f} m, {len(highest_detail_object.data.polygons)} faces at lod0"
    )


if "__main__" == __name__:
    main()
