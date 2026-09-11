"""Build and optionally export the X4 Andromeda scene with Blender 4.2."""

import argparse
import json
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

SOURCE_DIRECTORY = Path.home() / "x4mod/source"
SOURCE_STEM = "XMC"
SHIP_LENGTH = 2700.0
MATERIAL_NAME = "andromeda.andromeda_hull"
LOD_RATIO = (
    ("part_main", 1.0),
    ("part_main.LOD1", 0.55),
    ("part_main.LOD2", 0.25),
    ("part_main.LOD3", 0.1),
)
SAMPLE_RADIUS = 0.035
DORSAL_FACING = (0.0, 0.0, 0.0)
HULL_CORE_FRACTION = 0.12
MOUNT_SINK = 0.001
MAIN_WEAPON_TAGS = "combat extralarge andromeda weapon"
ENGINE_TAGS = "engine extralarge andromeda"
HULL_VERTEX_COLOUR = (0.18, 0.20, 0.22, 1.0)
HULL_TEXTURE_METRES = 120.0
FORWARD_FACING = (0.0, 0.0, 0.0)
ENGINE_SINK = 0.02

# Stable names and stations from the first shipped component, in Blender axes / ship length.
MOUNTS = (
    (
        "con_shieldgen_xl_01",
        "extralarge shield standard",
        "group_front_up_mid",
        (0.0, 0.19284192592592592, 0.10209603703703703),
    ),
    (
        "con_shieldgen_xl_02",
        "extralarge shield standard",
        "group_mid_up_mid",
        (0.0, -0.07246274074074074, 0.11030114814814816),
    ),
    (
        "con_shieldgen_xl_03",
        "extralarge shield standard",
        "group_front_down_mid",
        (0.0, 0.19284192592592592, -0.06689570370370371),
    ),
    (
        "con_shieldgen_xl_04",
        "extralarge shield standard",
        "group_mid_down_mid",
        (0.0, -0.07246274074074074, -0.11051148148148147),
    ),
    (
        "con_turret_001",
        "turret large standard missile hittable combat",
        "group_front_up_mid",
        (0.0, 0.34, -0.0023738362962962964),
    ),
    (
        "con_turret_002",
        "turret large standard missile hittable combat",
        "group_front_down_mid",
        (0.0, 0.34, -0.056736999999999996),
    ),
    (
        "con_turret_003",
        "turret large standard missile hittable combat",
        "group_mid_up_mid",
        (0.0, 0.12, 0.11171074074074075),
    ),
    (
        "con_turret_004",
        "turret large standard missile hittable combat",
        "group_mid_down_mid",
        (0.0, 0.12, -0.07186159259259259),
    ),
    (
        "con_turret_005",
        "turret large standard missile hittable combat",
        "group_mid_up_mid",
        (0.0, -0.14, 0.0693942962962963),
    ),
    (
        "con_turret_006",
        "turret large standard missile hittable combat",
        "group_mid_down_mid",
        (0.0, -0.14, -0.041415074074074076),
    ),
    (
        "con_turret_007",
        "turret medium standard missile hittable combat",
        "group_front_up_left",
        (-0.1995515925925926, 0.42, -0.046933333333333334),
    ),
    (
        "con_turret_008",
        "turret medium standard missile hittable combat",
        "group_front_down_left",
        (-0.1995515925925926, 0.42, -0.09523974074074074),
    ),
    (
        "con_turret_009",
        "turret medium standard missile hittable combat",
        "group_front_up_right",
        (0.19955151851851852, 0.42, -0.04693337037037037),
    ),
    (
        "con_turret_010",
        "turret medium standard missile hittable combat",
        "group_front_down_right",
        (0.19955151851851852, 0.42, -0.0952397037037037),
    ),
    (
        "con_turret_011",
        "turret medium standard missile hittable combat",
        "group_front_up_left",
        (-0.2355217777777778, 0.26, 0.010772437037037038),
    ),
    (
        "con_turret_012",
        "turret medium standard missile hittable combat",
        "group_front_down_left",
        (-0.2355217777777778, 0.26, -0.10729825925925927),
    ),
    (
        "con_turret_013",
        "turret medium standard missile hittable combat",
        "group_front_up_right",
        (0.2355217037037037, 0.26, 0.010772407407407408),
    ),
    (
        "con_turret_014",
        "turret medium standard missile hittable combat",
        "group_front_down_right",
        (0.2355217037037037, 0.26, -0.10729825925925927),
    ),
    (
        "con_turret_015",
        "turret medium standard missile hittable combat",
        "group_mid_up_left",
        (-0.25232133333333334, 0.08, 0.05372177777777778),
    ),
    (
        "con_turret_016",
        "turret medium standard missile hittable combat",
        "group_mid_down_left",
        (-0.25232133333333334, 0.08, -0.12699996296296295),
    ),
    (
        "con_turret_017",
        "turret medium standard missile hittable combat",
        "group_mid_up_right",
        (0.25232133333333334, 0.08, 0.05372177777777778),
    ),
    (
        "con_turret_018",
        "turret medium standard missile hittable combat",
        "group_mid_down_right",
        (0.25232133333333334, 0.08, -0.12699992592592593),
    ),
    (
        "con_turret_019",
        "turret medium standard missile hittable combat",
        "group_mid_up_left",
        (-0.2607861851851852, -0.12, -0.053059444444444444),
    ),
    (
        "con_turret_020",
        "turret medium standard missile hittable combat",
        "group_mid_down_left",
        (-0.2607861851851852, -0.12, -0.10685518518518519),
    ),
    (
        "con_turret_021",
        "turret medium standard missile hittable combat",
        "group_mid_up_right",
        (0.2607861851851852, -0.12, -0.053059481481481485),
    ),
    (
        "con_turret_022",
        "turret medium standard missile hittable combat",
        "group_mid_down_right",
        (0.2607861851851852, -0.12, -0.10685518518518519),
    ),
    (
        "con_turret_023",
        "turret medium standard missile hittable combat",
        "group_back_up_left",
        (-0.22315318518518518, -0.3, -0.017474462962962962),
    ),
    (
        "con_turret_024",
        "turret medium standard missile hittable combat",
        "group_back_down_left",
        (-0.22315318518518518, -0.3, -0.056842148148148156),
    ),
    (
        "con_turret_025",
        "turret medium standard missile hittable combat",
        "group_back_up_right",
        (0.22315322222222223, -0.3, -0.017474425925925928),
    ),
    (
        "con_turret_026",
        "turret medium standard missile hittable combat",
        "group_back_down_right",
        (0.22315322222222223, -0.3, -0.05684218518518518),
    ),
    (
        "con_turret_027",
        "turret medium standard missile hittable combat",
        "group_back_up_left",
        (-0.18413822222222223, -0.46, 0.08035837037037037),
    ),
    (
        "con_turret_028",
        "turret medium standard missile hittable combat",
        "group_back_down_left",
        (-0.18413822222222223, -0.46, -0.002666974074074074),
    ),
    (
        "con_turret_029",
        "turret medium standard missile hittable combat",
        "group_back_up_right",
        (0.1841382962962963, -0.46, 0.08035833333333334),
    ),
    (
        "con_turret_030",
        "turret medium standard missile hittable combat",
        "group_back_down_right",
        (0.1841382962962963, -0.46, -0.0026669985185185188),
    ),
    (
        "con_turret_031",
        "turret medium standard missile hittable combat",
        "group_front_up_left",
        (-0.055, 0.3, -0.0009001925925925926),
    ),
    (
        "con_turret_032",
        "turret medium standard missile hittable combat",
        "group_front_up_right",
        (0.055, 0.3, -0.0009002251851851852),
    ),
    (
        "con_turret_033",
        "turret medium standard missile hittable combat",
        "group_mid_up_left",
        (-0.055, 0.0, 0.12699996296296295),
    ),
    (
        "con_turret_034",
        "turret medium standard missile hittable combat",
        "group_mid_up_right",
        (0.055, 0.0, 0.12699996296296295),
    ),
    (
        "con_turret_035",
        "turret medium standard missile hittable combat",
        "group_back_up_left",
        (-0.055, -0.32, 0.11818748148148148),
    ),
    (
        "con_turret_036",
        "turret medium standard missile hittable combat",
        "group_back_up_right",
        (0.055, -0.32, 0.11818751851851851),
    ),
    (
        "con_shieldgen_m_001",
        "medium shield hittable standard",
        "group_back_down_left",
        (-0.21515318518518517, -0.315, -0.056842148148148156),
    ),
    (
        "con_shieldgen_m_002",
        "medium shield hittable standard",
        "group_back_down_right",
        (0.21515322222222222, -0.315, -0.05684218518518518),
    ),
    (
        "con_shieldgen_m_003",
        "medium shield hittable standard",
        "group_back_up_left",
        (-0.21515318518518517, -0.315, -0.017474462962962962),
    ),
    (
        "con_shieldgen_m_004",
        "medium shield hittable standard",
        "group_back_up_right",
        (0.21515322222222222, -0.315, -0.017474425925925928),
    ),
    (
        "con_shieldgen_m_005",
        "medium shield hittable standard",
        "group_front_down_left",
        (-0.1915515925925926, 0.40499999999999997, -0.09523974074074074),
    ),
    (
        "con_shieldgen_m_006",
        "medium shield hittable standard",
        "group_front_down_right",
        (0.1915515185185185, 0.40499999999999997, -0.0952397037037037),
    ),
    (
        "con_shieldgen_m_007",
        "medium shield hittable standard",
        "group_front_up_left",
        (-0.1915515925925926, 0.40499999999999997, -0.046933333333333334),
    ),
    (
        "con_shieldgen_m_008",
        "medium shield hittable standard",
        "group_front_up_right",
        (0.1915515185185185, 0.40499999999999997, -0.04693337037037037),
    ),
    (
        "con_shieldgen_m_009",
        "medium shield hittable standard",
        "group_mid_down_left",
        (-0.24432133333333333, 0.065, -0.12699996296296295),
    ),
    (
        "con_shieldgen_m_010",
        "medium shield hittable standard",
        "group_mid_down_right",
        (0.24432133333333333, 0.065, -0.12699992592592593),
    ),
    (
        "con_shieldgen_m_011",
        "medium shield hittable standard",
        "group_mid_up_left",
        (-0.24432133333333333, 0.065, 0.05372177777777778),
    ),
    (
        "con_shieldgen_m_012",
        "medium shield hittable standard",
        "group_mid_up_right",
        (0.24432133333333333, 0.065, 0.05372177777777778),
    ),
    (
        "con_shieldgen_m_013",
        "medium shield hittable standard",
        "group_engine_left",
        (-0.018, -0.23, 0.0),
    ),
    (
        "con_shieldgen_m_014",
        "medium shield hittable standard",
        "group_engine_right",
        (0.018, -0.23, 0.0),
    ),
)


def clear_scene():
    for item in list(bpy.data.objects):
        bpy.data.objects.remove(item, do_unlink=True)


def import_source():
    bpy.ops.wm.obj_import(
        filepath=str(SOURCE_DIRECTORY / f"{SOURCE_STEM}.obj"), forward_axis="Y", up_axis="Z"
    )
    imported = [item for item in bpy.context.scene.objects if "MESH" == item.type]
    bpy.ops.object.select_all(action="DESELECT")
    for item in imported:
        item.select_set(True)
    if not imported:
        raise ValueError("OBJ contains no mesh objects")
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


def repair_winding(mesh_object):
    mesh = mesh_object.data
    opposite = []
    for polygon in mesh.polygons:
        average = sum((mesh.corner_normals[i].vector for i in polygon.loop_indices), Vector())
        if polygon.normal.dot(average) < 0:
            opposite.append(polygon.index)
    if opposite:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()
        bmesh.ops.reverse_faces(bm, faces=[bm.faces[i] for i in opposite])
        bm.to_mesh(mesh)
        bm.free()
        print(f"andromeda: repaired {len(opposite)} faces from a legacy OBJ")
    bpy.context.view_layer.objects.active = mesh_object
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
    mesh.update()


def prepare_channels(mesh_object):
    mesh = mesh_object.data
    for layer in list(mesh.uv_layers):
        mesh.uv_layers.remove(layer)
    uv = mesh.uv_layers.new(name="uv1")
    for polygon in mesh.polygons:
        dominant = max(range(3), key=lambda axis: abs(polygon.normal[axis]))
        axes = ((1, 2), (0, 2), (0, 1))[dominant]
        for index in polygon.loop_indices:
            position = mesh.vertices[mesh.loops[index].vertex_index].co
            uv.data[index].uv = tuple(position[axis] / HULL_TEXTURE_METRES for axis in axes)
    for existing in list(mesh.color_attributes):
        mesh.color_attributes.remove(existing)
    for name, value in (
        ("col", HULL_VERTEX_COLOUR),
        ("idcode", (0.5, 0.5, 0.5, 1.0)),
        ("paintmodmask", (0.0, 0.0, 0.0, 1.0)),
    ):
        colour = mesh.color_attributes.new(name=name, type="BYTE_COLOR", domain="CORNER")
        for entry in colour.data:
            entry.color = value
    mesh_object.data.materials.clear()
    mesh_object.data.materials.append(
        (bpy.data.materials.get(MATERIAL_NAME) or bpy.data.materials.new(MATERIAL_NAME))
    )
    for polygon in mesh_object.data.polygons:
        polygon.use_smooth = True


def apply_modifiers(mesh_object):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    baked = bpy.data.meshes.new_from_object(mesh_object.evaluated_get(depsgraph))
    previous = mesh_object.data
    mesh_object.data = baked
    mesh_object.modifiers.clear()
    bpy.data.meshes.remove(previous)


def correct_shading(mesh_object):
    mesh = mesh_object.data
    bpy.context.view_layer.objects.active = mesh_object
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
    for _ in range(10):
        wrong = []
        for polygon in mesh.polygons:
            average = sum((mesh.corner_normals[i].vector for i in polygon.loop_indices), Vector())
            if polygon.normal.dot(average) <= 0:
                wrong.append(polygon)
        if not wrong:
            return
        for polygon in wrong:
            polygon.use_smooth = False
        mesh.update()
    raise ValueError(f"{mesh_object.name}: could not produce consistent shading normals")


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
        correct_shading(mesh_object)
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
    if hasattr(empty, "groups") and group is not None:
        empty.groups = group
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


class HullSurface:
    def __init__(self, mesh):
        self.tree = BVHTree.FromPolygons(
            [v.co for v in mesh.vertices], [list(p.vertices) for p in mesh.polygons]
        )
        self.height = max(abs(v.co.z) for v in mesh.vertices) + SHIP_LENGTH

    def at(self, seed, upward, name):
        sign = 1.0 if upward else -1.0
        start = Vector((seed[0], seed[1], sign * self.height))
        hit, normal, _, _ = self.tree.ray_cast(start, Vector((0, 0, -sign)), 2 * self.height)
        if hit is None:
            candidates = [
                entry
                for entry in self.tree.find_nearest_range(Vector(seed), SHIP_LENGTH * SAMPLE_RADIUS)
                if entry[1].z * sign > 0
            ]
            if candidates:
                hit, normal, _, _ = min(candidates, key=lambda entry: entry[3])
            if hit is not None:
                print(f"andromeda: {name} snapped to nearby surface at {tuple(hit)}")
        if hit is None or normal.z * sign <= 0:
            raise ValueError(f"{name}: no outward-facing hull surface near {tuple(seed)}")
        return hit, normal.normalized()


def longitudinal_facing(normal):
    normal = normal.normalized()
    forward = Vector((0, 1, 0))
    forward -= normal * forward.dot(normal)
    if forward.length < 1e-6:
        raise ValueError("mount normal leaves no longitudinal direction on the hull")
    forward.normalize()
    right = forward.cross(normal).normalized()
    return Matrix((right, forward, normal)).transposed().to_euler()


def place_mounts(surface):
    for name, tags, group, coordinates in MOUNTS:
        upward = "_up_" in group or group.startswith("group_engine_")
        seed = Vector(coordinates) * SHIP_LENGTH
        point, normal = surface.at(seed, upward, name)
        point -= normal * (SHIP_LENGTH * MOUNT_SINK)
        facing = (
            longitudinal_facing(normal)
            if "shield" in tags.split()
            else normal.to_track_quat("Z", "Y").to_euler()
        )
        add_connection(name, tags, point, 1.0, facing, group)


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


def place_fixed(vertex, points, factor, center, surface):
    core = hull_core(vertex)
    core_aft = min(c.y for c in core)
    core_fore = max(c.y for c in core)
    bridge, _ = surface.at((0.0, core_fore * 0.55, 0.0), True, "con_cockpit")
    add_connection("con_cockpit", "cockpit cockpit_visible", bridge, 1.0, DORSAL_FACING)
    add_connection("con_playercontrol", "playercontrol", bridge, 1.0, DORSAL_FACING)
    add_connection("con_storage01", "storage", (0.0, 0.0, 0.0), 2.0, None, "group_mid_up_mid")
    add_connection("con_shiptrader", "shiptrader", (0.0, core_aft * 0.3, 0.0))
    engine_x = SHIP_LENGTH * 0.018
    for engine_index, side in enumerate((-1.0, 1.0)):
        add_connection(
            f"con_engine_{engine_index + 1:02d}",
            ENGINE_TAGS,
            (side * engine_x, core_aft + SHIP_LENGTH * ENGINE_SINK, 0.0),
            1.6,
            None,
            f"group_engine_{'left' if 0.0 > side else 'right'}",
        )
    for weapon_index, tip in enumerate(arm_tips(vertex)):
        add_connection(
            f"con_weapon_xl_{weapon_index + 1:02d}",
            MAIN_WEAPON_TAGS,
            tip,
            2.0,
            FORWARD_FACING,
            None,
        )
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
    return dock_index


def main():
    global SOURCE_DIRECTORY
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--source", type=Path, default=SOURCE_DIRECTORY)
    parser.add_argument("--export", action="store_true")
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    option = parser.parse_args(arguments)
    SOURCE_DIRECTORY = option.source
    if option.export and "[assets]" not in str(option.target):
        raise ValueError("Egosoft export requires [assets] in the target path")
    if bpy.app.version[:2] != (4, 2):
        raise ValueError("use Blender 4.2 with the Egosoft extensions")
    clear_scene()
    source = import_source()
    repair_winding(source)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from andromeda_turrets import TAGS, remove_from_hull

    turret_stations = remove_from_hull(source)
    factor, center = normalize(source)
    prepare_channels(source)
    made = build_parts(source)
    surface = HullSurface(made[0].data)
    bpy.data.objects.remove(source, do_unlink=True)
    vertex = [v.co.copy() for v in made[0].data.vertices]
    points = json.loads(
        (SOURCE_DIRECTORY / f"{SOURCE_STEM}_points.json").read_text(encoding="utf-8")
    )
    place_mounts(surface)
    for index, (pivot, frame) in enumerate(turret_stations, 1):
        location = (pivot - center) * factor
        add_connection(
            f"con_turret_integrated_{index:02d}",
            TAGS,
            location,
            facing=frame.to_euler(),
            group=group_for(location, frame[2][2] > 0),
        )
    docks = place_fixed(vertex, points, factor, center, surface)
    if hasattr(bpy.context.scene, "classAttr"):
        bpy.context.scene.classAttr = "ship_xl"
    elif option.export:
        raise RuntimeError("enable the Egosoft extensions before exporting")
    option.target.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(option.target))
    print(f"andromeda: {SHIP_LENGTH:.0f} m, scale {factor:.4f}")
    print(
        f"andromeda: 6 standard large turrets, 4 integrated twin turrets, 30 medium turrets, 4 XL shields, 14 local shields, {docks} docking bays"
    )
    for item in made:
        print(f"  {item.name}: {len(item.data.polygons)} faces")
    if option.export:
        for item in bpy.context.scene.objects:
            if item.get("group_name"):
                item.groups = item["group_name"]
        dae = option.target.with_name(option.target.stem + "_data.dae")
        xml = option.target.with_suffix(".xml")
        for output in (dae, xml):
            if output.exists():
                output.unlink()
        bpy.ops.ego_tools.export_data(write_xml=True)
        if not dae.is_file() or not xml.is_file():
            raise RuntimeError("Egosoft exporter did not produce both DAE and component XML")


if "__main__" == __name__:
    main()
