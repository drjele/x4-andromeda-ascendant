"""Build the X4-ready Andromeda scene in Blender 4.2 from the converted mesh."""

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

SOURCE_DIRECTORY = Path.home() / "x4mod/source"
SOURCE_STEM = "XMC"
SHIP_LENGTH = 2422.0
MATERIAL_NAME = "andromeda.andromeda_hull"
LOD_RATIO = (
    ("part_main", 1.0),
    ("part_main.LOD1", 0.55),
    ("part_main.LOD2", 0.25),
    ("part_main.LOD3", 0.1),
)
TURRET_MEDIUM_TAGS = "turret medium standard missile hittable combat"
TURRET_LARGE_TAGS = "turret large standard missile hittable combat"
SHIELD_LARGE_TAGS = "extralarge shield standard"
SHIELD_MEDIUM_TAGS = "medium shield hittable standard"
LARGE_TURRET_STATIONS = (0.34, 0.12, -0.14, -0.38)
ARM_TURRET_STATIONS = (0.42, 0.26, 0.08, -0.12, -0.3, -0.46)
FLANK_TURRET_STATIONS = (0.3, 0.0, -0.32)
SAMPLE_RADIUS = 0.035


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_source():
    bpy.ops.wm.obj_import(
        filepath=str(SOURCE_DIRECTORY / f"{SOURCE_STEM}.obj"), forward_axis="Y", up_axis="Z"
    )
    imported = [item for item in bpy.context.scene.objects if "MESH" == item.type]
    bpy.ops.object.select_all(action="DESELECT")
    for item in imported:
        item.select_set(True)
    bpy.context.view_layer.objects.active = imported[0]
    if 1 < len(imported):
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def normalize(mesh_object):
    corner = [vertex.co for vertex in mesh_object.data.vertices]
    low = Vector((min(c.x for c in corner), min(c.y for c in corner), min(c.z for c in corner)))
    high = Vector((max(c.x for c in corner), max(c.y for c in corner), max(c.z for c in corner)))
    length = high.y - low.y
    if 0.0 == length:
        raise ValueError("source mesh has no length along the forward axis")
    factor = SHIP_LENGTH / length
    center = (low + high) * 0.5
    for vertex in mesh_object.data.vertices:
        vertex.co = (vertex.co - center) * factor
    mesh_object.data.update()
    return factor, center


def prepare_channels(mesh_object):
    for layer in mesh_object.data.uv_layers:
        layer.name = "uv1"
    if 0 == len(mesh_object.data.color_attributes):
        mesh_object.data.color_attributes.new(name="col", type="BYTE_COLOR", domain="CORNER")
    mesh_object.data.materials.clear()
    mesh_object.data.materials.append(bpy.data.materials.new(MATERIAL_NAME))


def apply_modifiers(mesh_object):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    baked = bpy.data.meshes.new_from_object(mesh_object.evaluated_get(depsgraph))
    previous = mesh_object.data
    mesh_object.data = baked
    mesh_object.modifiers.clear()
    bpy.data.meshes.remove(previous)


def build_parts(source):
    made = []
    for name, ratio in LOD_RATIO:
        mesh = source.data.copy()
        mesh_object = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(mesh_object)
        if 1.0 > ratio:
            modifier = mesh_object.modifiers.new(name="decimate", type="DECIMATE")
            modifier.ratio = ratio
            apply_modifiers(mesh_object)
        mesh_object.data.name = name
        made.append(mesh_object)
    wreck = bpy.data.objects.new("part_main.wreck", made[1].data.copy())
    bpy.context.scene.collection.objects.link(wreck)
    return made


def add_connection(name, tags, location, size=1.0):
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "ARROWS"
    empty.empty_display_size = SHIP_LENGTH * 0.012 * size
    empty.location = location
    bpy.context.scene.collection.objects.link(empty)
    empty["extratags"] = tags
    return empty


def surface_at(vertex, x_target, y_target, radius, upward):
    near = [c for c in vertex if abs(c.x - x_target) < radius and abs(c.y - y_target) < radius]
    if 0 == len(near):
        return None
    best = max(near, key=lambda c: c.z) if True == upward else min(near, key=lambda c: c.z)
    return Vector((x_target, y_target, best.z))


def arm_offset(vertex, y_target, side, radius):
    near = [c for c in vertex if abs(c.y - y_target) < radius and 0.0 < c.x * side]
    if 0 == len(near):
        return None
    return max(near, key=lambda c: abs(c.x)).x


def place_turrets(vertex):
    radius = SHIP_LENGTH * SAMPLE_RADIUS
    index = 0
    for station in LARGE_TURRET_STATIONS:
        y = station * SHIP_LENGTH
        for upward in (True, False):
            point = surface_at(vertex, 0.0, y, radius, upward)
            if None is point:
                continue
            index += 1
            add_connection(f"con_turret_{index:03d}", TURRET_LARGE_TAGS, point, 1.6)
    large_count = index
    for station in ARM_TURRET_STATIONS:
        y = station * SHIP_LENGTH
        for side in (-1.0, 1.0):
            x = arm_offset(vertex, y, side, radius)
            if None is x:
                continue
            for upward in (True, False):
                point = surface_at(vertex, x * 0.92, y, radius, upward)
                if None is point:
                    continue
                index += 1
                add_connection(f"con_turret_{index:03d}", TURRET_MEDIUM_TAGS, point)
    for station in FLANK_TURRET_STATIONS:
        y = station * SHIP_LENGTH
        for side in (-1.0, 1.0):
            point = surface_at(vertex, side * SHIP_LENGTH * 0.055, y, radius, True)
            if None is point:
                continue
            index += 1
            add_connection(f"con_turret_{index:03d}", TURRET_MEDIUM_TAGS, point)
    return large_count, index - large_count


def place_fixed(vertex, points, factor, center):
    top = max(c.z for c in vertex)
    aft = min(c.y for c in vertex)
    fore = max(c.y for c in vertex)
    add_connection("con_cockpit", "cockpit cockpit_visible", (0.0, fore * 0.42, top * 0.6))
    add_connection("con_playercontrol", "playercontrol", (0.0, fore * 0.42, top * 0.6))
    add_connection("con_storage01", "storage", (0.0, 0.0, 0.0), 2.0)
    add_connection("con_shiptrader", "shiptrader", (0.0, aft * 0.2, 0.0))
    add_connection(
        "con_engine_01", "engine extralarge standard", (-SHIP_LENGTH * 0.028, aft, 0.0), 1.6
    )
    add_connection(
        "con_engine_02", "engine extralarge standard", (SHIP_LENGTH * 0.028, aft, 0.0), 1.6
    )
    for shield_index, along in enumerate((0.4, 0.18, -0.05, -0.28, -0.45, 0.0)):
        add_connection(
            f"con_shieldgen_xl_{shield_index + 1:02d}",
            SHIELD_LARGE_TAGS,
            (0.0, fore * along, top * 0.35),
            1.4,
        )
    medium_index = 0
    for along in (0.35, 0.1, -0.15, -0.4):
        for side in (-1.0, 1.0):
            for upward in (True, False):
                medium_index += 1
                add_connection(
                    f"con_shieldgen_m_{medium_index:02d}",
                    SHIELD_MEDIUM_TAGS,
                    (side * SHIP_LENGTH * 0.08, fore * along, top * (0.25 if upward else -0.25)),
                )
    for cm_index, side in enumerate((-1.0, 1.0, -1.0, 1.0)):
        add_connection(
            f"con_countermeasure_{cm_index + 1:02d}",
            "countermeasures",
            (side * SHIP_LENGTH * 0.04, aft * (0.5 if 2 > cm_index else 0.2), 0.0),
        )
    dock_index = 0
    for entry in points:
        if "Hangar" != entry["name"]:
            continue
        dock_index += 1
        location = (Vector(entry["position"]) - center) * factor
        add_connection(f"con_dockingbay_{dock_index:02d}", "dockingbay", location, 2.0)
    return medium_index, dock_index


def main():
    target = Path(sys.argv[-1]) if 1 < len(sys.argv) else Path.home() / "andromeda.blend"
    clear_scene()
    source = import_source()
    factor, center = normalize(source)
    prepare_channels(source)
    made = build_parts(source)
    bpy.data.objects.remove(source, do_unlink=True)
    vertex = [v.co for v in made[0].data.vertices]
    points = json.loads(
        (SOURCE_DIRECTORY / f"{SOURCE_STEM}_points.json").read_text(encoding="utf-8")
    )
    large, medium = place_turrets(vertex)
    shields, docks = place_fixed(vertex, points, factor, center)
    try:
        bpy.context.scene.classAttr = "ship_xl"
    except (AttributeError, TypeError):
        pass
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    print(f"andromeda: {SHIP_LENGTH:.0f} m, scale {factor:.4f}")
    print(f"andromeda: {large} large turrets, {medium} medium turrets")
    print(f"andromeda: {shields} medium shields, {docks} docking bays")
    for item in made:
        print(f"  {item.name}: {len(item.data.polygons)} faces")


if "__main__" == __name__:
    main()
