"""
Andromeda Ascendant - procedural hull generator for Blender 4.2

Run: Scripting tab -> New -> paste -> Run Script.
Rerunning wipes the previous result, so iteration is safe.

Axis convention: +Y forward, +Z up (matches the X4 hard-point export settings).
Everything is driven by SHIP_LENGTH; all profile numbers are fractions of it,
so changing the length rescales the whole ship coherently.
"""

import bmesh
import bpy
from mathutils import Vector

SHIP_LENGTH = 1300.0

# (t, half_width, half_height, vertical_offset) as fractions of SHIP_LENGTH.
# t = 0.0 is the tip of the prow, t = 1.0 is the stern plane.
# This table is the shape. Tune it, rerun, look, repeat.
HULL_PROFILE = [
    (0.000, 0.0000, 0.0000,  0.000),
    (0.040, 0.0066, 0.0060, -0.002),
    (0.110, 0.0182, 0.0140, -0.004),
    (0.220, 0.0319, 0.0230, -0.006),
    (0.350, 0.0468, 0.0320, -0.007),
    (0.480, 0.0649, 0.0410, -0.008),
    (0.600, 0.0798, 0.0470, -0.008),
    (0.700, 0.0836, 0.0490, -0.007),
    (0.820, 0.0770, 0.0470, -0.005),
    (0.920, 0.0649, 0.0430, -0.003),
    (1.000, 0.0523, 0.0390,  0.000),
]

# Superellipse exponents: higher = boxier. Ships read better with a flatter
# belly than deck, hence the split.
TOP_EXPONENT = 2.4
BOTTOM_EXPONENT = 3.4

NACELLE_START_T = 0.640
NACELLE_LATERAL = 0.0750
NACELLE_HALF_WIDTH = 0.0220
NACELLE_HALF_HEIGHT = 0.0240

FIN_START_T = 0.560
FIN_END_T = 0.910
FIN_HEIGHT = 0.0680
FIN_SWEEP = 0.0700
FIN_LATERAL = 0.0300
FIN_THICKNESS = 0.0060

RING_SEGMENTS = 24
LOD_RING_SEGMENTS = (24, 16, 10, 6)
LOD_PROFILE_STRIDE = (1, 1, 2, 3)

TURRET_ROWS_DORSAL = 4
TURRET_ROWS_VENTRAL = 4
TURRET_SPAN_T = (0.300, 0.880)

COLLECTION_NAME = "andromeda_ascendant"


def clear_previous():
    existing = bpy.data.collections.get(COLLECTION_NAME)
    if existing is None:
        return
    for obj in list(existing.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(existing)


def make_collection():
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)
    return collection


def superellipse_point(angle_index, segments, half_width, half_height):
    import math

    theta = 2.0 * math.pi * angle_index / segments
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    exponent = TOP_EXPONENT if sin_t >= 0.0 else BOTTOM_EXPONENT
    x = half_width * math.copysign(abs(cos_t) ** (2.0 / exponent), cos_t)
    z = half_height * math.copysign(abs(sin_t) ** (2.0 / exponent), sin_t)
    return x, z


def sample_profile(stride):
    if 1 == stride:
        return list(HULL_PROFILE)
    sampled = HULL_PROFILE[::stride]
    if sampled[-1] != HULL_PROFILE[-1]:
        sampled.append(HULL_PROFILE[-1])
    if sampled[0] != HULL_PROFILE[0]:
        sampled.insert(0, HULL_PROFILE[0])
    return sampled


def build_hull_mesh(name, segments, stride):
    profile = sample_profile(stride)
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    rings = []
    for t, half_width, half_height, offset in profile:
        y = (0.5 - t) * SHIP_LENGTH
        z_center = offset * SHIP_LENGTH

        if 0.0 == half_width and 0.0 == half_height:
            rings.append([bm.verts.new((0.0, y, z_center))])
            continue

        ring = []
        for i in range(segments):
            x, z = superellipse_point(i, segments, half_width, half_height)
            ring.append(bm.verts.new((x * SHIP_LENGTH, y, z_center + z * SHIP_LENGTH)))
        rings.append(ring)

    bm.verts.ensure_lookup_table()

    for index in range(len(rings) - 1):
        current = rings[index]
        following = rings[index + 1]

        if 1 == len(current):
            apex = current[0]
            for i in range(segments):
                bm.faces.new((apex, following[i], following[(i + 1) % segments]))
            continue

        for i in range(segments):
            j = (i + 1) % segments
            bm.faces.new((current[i], current[j], following[j], following[i]))

    stern = rings[-1]
    bm.faces.new(tuple(reversed(stern)))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def build_nacelle_mesh(name, side, segments):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    stations = [
        (NACELLE_START_T, 0.30, 0.35),
        (0.720, 0.80, 0.85),
        (0.850, 1.00, 1.00),
        (0.960, 0.95, 0.95),
        (1.000, 0.80, 0.80),
    ]

    rings = []
    for t, width_scale, height_scale in stations:
        y = (0.5 - t) * SHIP_LENGTH
        x_center = side * NACELLE_LATERAL * SHIP_LENGTH
        ring = []
        for i in range(segments):
            x, z = superellipse_point(
                i,
                segments,
                NACELLE_HALF_WIDTH * width_scale,
                NACELLE_HALF_HEIGHT * height_scale,
            )
            ring.append(bm.verts.new((x_center + x * SHIP_LENGTH, y, z * SHIP_LENGTH)))
        rings.append(ring)

    bm.verts.ensure_lookup_table()

    for index in range(len(rings) - 1):
        current = rings[index]
        following = rings[index + 1]
        for i in range(segments):
            j = (i + 1) % segments
            bm.faces.new((current[i], current[j], following[j], following[i]))

    bm.faces.new(tuple(rings[0]))
    bm.faces.new(tuple(reversed(rings[-1])))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def build_fin_mesh(name, side):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    root_front_y = (0.5 - FIN_START_T) * SHIP_LENGTH
    root_rear_y = (0.5 - FIN_END_T) * SHIP_LENGTH
    tip_front_y = root_front_y - FIN_SWEEP * SHIP_LENGTH
    tip_rear_y = root_rear_y - FIN_SWEEP * 0.4 * SHIP_LENGTH

    x_root = side * FIN_LATERAL * SHIP_LENGTH
    x_tip = side * FIN_LATERAL * 0.55 * SHIP_LENGTH
    z_root = 0.030 * SHIP_LENGTH
    z_tip = FIN_HEIGHT * SHIP_LENGTH

    half = FIN_THICKNESS * 0.5 * SHIP_LENGTH
    outline = [
        (x_root, root_front_y, z_root),
        (x_root, root_rear_y, z_root),
        (x_tip, tip_rear_y, z_tip),
        (x_tip, tip_front_y, z_tip),
    ]

    near = [bm.verts.new((x - half * side, y, z)) for x, y, z in outline]
    far = [bm.verts.new((x + half * side, y, z)) for x, y, z in outline]
    bm.verts.ensure_lookup_table()

    bm.faces.new(near)
    bm.faces.new(tuple(reversed(far)))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((near[i], near[j], far[j], far[i]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def new_object(collection, name, mesh):
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def join_into_lod(collection, lod_index):
    segments = LOD_RING_SEGMENTS[lod_index]
    stride = LOD_PROFILE_STRIDE[lod_index]
    suffix = f"_lod{lod_index}"

    parts = [
        new_object(collection, f"hull{suffix}", build_hull_mesh(f"hull{suffix}", segments, stride)),
        new_object(collection, f"nacelle_l{suffix}", build_nacelle_mesh(f"nacelle_l{suffix}", -1, segments)),
        new_object(collection, f"nacelle_r{suffix}", build_nacelle_mesh(f"nacelle_r{suffix}", 1, segments)),
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
    obj = new_object(collection, "andromeda_collision", mesh)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=True)
    bm.to_mesh(mesh)
    bm.free()

    modifier = obj.modifiers.new(name="decimate", type="DECIMATE")
    modifier.ratio = 0.4
    return obj


def hull_half_height_at(t):
    for index in range(len(HULL_PROFILE) - 1):
        t0, _, h0, o0 = HULL_PROFILE[index]
        t1, _, h1, o1 = HULL_PROFILE[index + 1]
        if t0 <= t <= t1:
            span = t1 - t0
            factor = 0.0 if 0.0 == span else (t - t0) / span
            return (h0 + (h1 - h0) * factor, o0 + (o1 - o0) * factor)
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
        t = start_t + (end_t - start_t) * row / max(1, TURRET_ROWS_DORSAL - 1)
        half_height, offset = hull_half_height_at(t)
        y = (0.5 - t) * SHIP_LENGTH
        z = (offset + half_height) * SHIP_LENGTH
        place_empty(collection, f"con_turret_{row * 2 + 1:03d}", (0.0, y, z), display)

    for row in range(TURRET_ROWS_VENTRAL):
        t = start_t + (end_t - start_t) * row / max(1, TURRET_ROWS_VENTRAL - 1)
        half_height, offset = hull_half_height_at(t)
        y = (0.5 - t) * SHIP_LENGTH
        z = (offset - half_height) * SHIP_LENGTH
        place_empty(collection, f"con_turret_{row * 2 + 2:03d}", (0.0, y, z), display)

    for index, t in enumerate((0.400, 0.560, 0.720, 0.860)):
        half_height, offset = hull_half_height_at(t)
        y = (0.5 - t) * SHIP_LENGTH
        place_empty(
            collection,
            f"con_shield_{index + 1:02d}",
            (0.0, y, offset * SHIP_LENGTH),
            display,
        )

    half_height, offset = hull_half_height_at(0.660)
    place_empty(
        collection,
        "con_dock_01",
        (0.0, (0.5 - 0.660) * SHIP_LENGTH, (offset - half_height) * SHIP_LENGTH),
        display * 2.0,
    )

    half_height, offset = hull_half_height_at(0.180)
    place_empty(
        collection,
        "con_cockpit",
        (0.0, (0.5 - 0.180) * SHIP_LENGTH, (offset + half_height * 0.6) * SHIP_LENGTH),
        display,
    )


def main():
    clear_previous()
    collection = make_collection()

    lod0 = None
    for lod_index in range(len(LOD_RING_SEGMENTS)):
        merged = join_into_lod(collection, lod_index)
        if 0 == lod_index:
            lod0 = merged

    build_collision(collection, lod0)
    build_connections(collection)

    print(f"andromeda: {SHIP_LENGTH:.0f} m, {len(lod0.data.polygons)} faces at lod0")


if "__main__" == __name__:
    main()
