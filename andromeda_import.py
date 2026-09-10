"""Build the X4-ready Andromeda scene in Blender 4.2 from the converted mesh."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

SOURCE_DIRECTORY = Path.home() / "x4mod/source"
SOURCE_STEM = "XMC"
SHIP_LENGTH = 2700.0
MATERIAL_NAME = "andromeda.andromeda_hull"
HULL_VERTEX_COLOUR = (0.72, 0.73, 0.75, 1.0)
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
DORSAL_FACING = (0.0, 0.0, 0.0)
VENTRAL_FACING = (math.pi, 0.0, 0.0)
HULL_CORE_FRACTION = 0.12
MOUNT_SINK = 0.004
SHIELD_DORSAL_STATIONS = (0.5, -0.25)
SHIELD_VENTRAL_STATIONS = (0.5, -0.25)
MAIN_WEAPON_TAGS = "combat extralarge mandatory ship_kha_xl_battleship_01 weapon"
FORWARD_FACING = (-math.pi / 2.0, 0.0, 0.0)
ENGINE_SINK = 0.02


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
    for existing in list(mesh_object.data.color_attributes):
        mesh_object.data.color_attributes.remove(existing)
    colour = mesh_object.data.color_attributes.new(name="col", type="BYTE_COLOR", domain="CORNER")
    for entry in colour.data:
        entry.color = HULL_VERTEX_COLOUR
    mesh_object.data.materials.clear()
    mesh_object.data.materials.append(bpy.data.materials.new(MATERIAL_NAME))
    for polygon in mesh_object.data.polygons:
        polygon.use_smooth = True


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


def add_connection(name, tags, location, size=1.0, facing=None, group=None):
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "ARROWS"
    empty.empty_display_size = SHIP_LENGTH * 0.012 * size
    empty.location = location
    if None is not facing:
        empty.rotation_euler = facing
    bpy.context.scene.collection.objects.link(empty)
    empty["extratags"] = tags
    if None is not group:
        empty["group_name"] = group
    return empty


def station_name(y_value):
    if y_value > SHIP_LENGTH * 0.15:
        return "front"
    if y_value < -SHIP_LENGTH * 0.15:
        return "back"
    return "mid"


def side_name(x_value):
    if x_value > SHIP_LENGTH * 0.02:
        return "right"
    if x_value < -SHIP_LENGTH * 0.02:
        return "left"
    return "mid"


def group_for(location, upward):
    vertical = "up" if True == upward else "down"
    return f"group_{station_name(location[1])}_{vertical}_{side_name(location[0])}"


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
            add_connection(
                f"con_turret_{index:03d}",
                TURRET_LARGE_TAGS,
                sink(point, upward),
                1.6,
                DORSAL_FACING if True == upward else VENTRAL_FACING,
                group_for(point, upward),
            )
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
                add_connection(
                    f"con_turret_{index:03d}",
                    TURRET_MEDIUM_TAGS,
                    sink(point, upward),
                    1.0,
                    DORSAL_FACING if True == upward else VENTRAL_FACING,
                    group_for(point, upward),
                )
    for station in FLANK_TURRET_STATIONS:
        y = station * SHIP_LENGTH
        for side in (-1.0, 1.0):
            point = surface_at(vertex, side * SHIP_LENGTH * 0.055, y, radius, True)
            if None is point:
                continue
            index += 1
            add_connection(
                f"con_turret_{index:03d}",
                TURRET_MEDIUM_TAGS,
                sink(point, True),
                1.0,
                DORSAL_FACING,
                group_for(point, True),
            )
    return large_count, index - large_count


def sink(point, upward):
    depth = SHIP_LENGTH * MOUNT_SINK
    return Vector((point[0], point[1], point[2] - depth if True == upward else point[2] + depth))


def arm_tips(vertex):
    half_width = max(abs(c.x) for c in vertex)
    tips = []
    for side in (-1.0, 1.0):
        arm = [c for c in vertex if 0.0 < c.x * side and abs(c.x) > 0.5 * half_width]
        if 0 == len(arm):
            continue
        tips.append(max(arm, key=lambda c: c.y))
    return tips


def hull_core(vertex):
    half_width = max(abs(c.x) for c in vertex)
    core = [c for c in vertex if abs(c.x) < HULL_CORE_FRACTION * half_width]
    return core if 0 < len(core) else vertex


def place_fixed(vertex, points, factor, center):
    core = hull_core(vertex)
    core_aft = min(c.y for c in core)
    core_fore = max(c.y for c in core)
    radius = SHIP_LENGTH * SAMPLE_RADIUS
    bridge = surface_at(vertex, 0.0, core_fore * 0.55, radius, True)
    if None is bridge:
        bridge = Vector((0.0, core_fore * 0.55, 0.0))
    add_connection("con_cockpit", "cockpit cockpit_visible", bridge, 1.0, DORSAL_FACING)
    add_connection("con_playercontrol", "playercontrol", bridge, 1.0, DORSAL_FACING)
    add_connection("con_storage01", "storage", (0.0, 0.0, 0.0), 2.0, None, "group_mid_up_mid")
    add_connection("con_shiptrader", "shiptrader", (0.0, core_aft * 0.3, 0.0))
    engine_x = SHIP_LENGTH * 0.018
    for engine_index, side in enumerate((-1.0, 1.0)):
        add_connection(
            f"con_engine_{engine_index + 1:02d}",
            "engine extralarge standard",
            (side * engine_x, core_aft + SHIP_LENGTH * ENGINE_SINK, 0.0),
            1.6,
            None,
            f"group_back_down_{'left' if 0.0 > side else 'right'}",
        )
    for weapon_index, tip in enumerate(arm_tips(vertex)):
        add_connection(
            f"con_weapon_xl_{weapon_index + 1:02d}",
            MAIN_WEAPON_TAGS,
            tip,
            2.0,
            FORWARD_FACING,
            f"group_front_up_{'left' if 0.0 > tip[0] else 'right'}",
        )
    shield_index = 0
    for along in SHIELD_DORSAL_STATIONS:
        y = core_fore * along if 0.0 < along else core_aft * -along
        point = surface_at(vertex, 0.0, y, radius, True)
        if None is point:
            continue
        shield_index += 1
        add_connection(
            f"con_shieldgen_xl_{shield_index:02d}",
            SHIELD_LARGE_TAGS,
            sink(point, True),
            1.4,
            DORSAL_FACING,
            group_for(point, True),
        )
    for along in SHIELD_VENTRAL_STATIONS:
        y = core_fore * along if 0.0 < along else core_aft * -along
        point = surface_at(vertex, 0.0, y, radius, False)
        if None is point:
            continue
        shield_index += 1
        add_connection(
            f"con_shieldgen_xl_{shield_index:02d}",
            SHIELD_LARGE_TAGS,
            sink(point, False),
            1.4,
            VENTRAL_FACING,
            group_for(point, False),
        )
    medium_index = 0
    for cm_index, side in enumerate((-1.0, 1.0, -1.0, 1.0)):
        add_connection(
            f"con_countermeasure_{cm_index + 1:02d}",
            "countermeasures",
            (side * SHIP_LENGTH * 0.03, core_aft * (0.6 if 2 > cm_index else 0.25), 0.0),
            1.0,
            None,
            f"group_back_down_{'left' if 0.0 > side else 'right'}",
        )
    dock_index = 0
    for entry in points:
        if "Hangar" != entry["name"]:
            continue
        dock_index += 1
        location = (Vector(entry["position"]) - center) * factor
        add_connection(
            f"con_dockingbay_{dock_index:02d}",
            "dockingbay",
            location,
            2.0,
            None,
            group_for(location, True),
        )
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
