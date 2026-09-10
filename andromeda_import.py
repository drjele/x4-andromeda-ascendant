"""Import the converted Andromeda mesh into Blender 4.2 and prepare it for X4 export."""

import json
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

SOURCE_DIRECTORY = Path.home() / "andromeda"
SOURCE_STEM = "XMC"
SHIP_LENGTH = 1300.0
COLLECTION_NAME = "andromeda_ascendant"
LOD_RATIO = (1.0, 0.55, 0.25, 0.1)
COLLISION_RATIO = 0.05
ENGINE_CORE_FRACTION = 0.12
ENGINE_LATERAL_FRACTION = 0.35
TURRET_POINT_NAME = ("Weapon-0", "Weapon-1")
DOCK_POINT_NAME = ("Hangar",)


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


def import_source(collection):
    before = set(bpy.context.scene.objects)
    bpy.ops.wm.obj_import(
        filepath=str(SOURCE_DIRECTORY / f"{SOURCE_STEM}.obj"), forward_axis="Y", up_axis="Z"
    )
    imported = [item for item in bpy.context.scene.objects if item not in before]
    bpy.ops.object.select_all(action="DESELECT")
    for item in imported:
        item.select_set(True)
    bpy.context.view_layer.objects.active = imported[0]
    if 1 < len(imported):
        bpy.ops.object.join()
    merged = bpy.context.view_layer.objects.active
    for source_collection in list(merged.users_collection):
        source_collection.objects.unlink(merged)
    collection.objects.link(merged)
    return merged


def world_bounds(mesh_object):
    corner = [mesh_object.matrix_world @ vertex.co for vertex in mesh_object.data.vertices]
    low = Vector((min(c.x for c in corner), min(c.y for c in corner), min(c.z for c in corner)))
    high = Vector((max(c.x for c in corner), max(c.y for c in corner), max(c.z for c in corner)))
    return low, high


def normalize(mesh_object):
    low, high = world_bounds(mesh_object)
    length = high.y - low.y
    if 0.0 == length:
        raise ValueError("source mesh has no length along the forward axis")
    factor = SHIP_LENGTH / length
    center = (low + high) * 0.5
    for vertex in mesh_object.data.vertices:
        vertex.co = (vertex.co - center) * factor
    mesh_object.data.update()
    return factor, center


def build_lod(collection, source, lod_index):
    mesh = source.data.copy()
    mesh.name = f"andromeda_lod{lod_index}"
    mesh_object = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(mesh_object)
    ratio = LOD_RATIO[lod_index]
    if 1.0 > ratio:
        modifier = mesh_object.modifiers.new(name="decimate", type="DECIMATE")
        modifier.ratio = ratio
        apply_modifiers(mesh_object)
    return mesh_object


def apply_modifiers(mesh_object):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh_object.evaluated_get(depsgraph)
    baked = bpy.data.meshes.new_from_object(evaluated)
    baked.name = mesh_object.data.name
    previous = mesh_object.data
    mesh_object.data = baked
    mesh_object.modifiers.clear()
    bpy.data.meshes.remove(previous)


def build_collision(collection, source):
    mesh = source.data.copy()
    mesh.name = "andromeda_collision"
    mesh_object = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(mesh_object)
    mesh_builder = bmesh.new()
    mesh_builder.from_mesh(mesh)
    result = bmesh.ops.convex_hull(mesh_builder, input=mesh_builder.verts, use_existing_faces=False)
    bmesh.ops.delete(
        mesh_builder,
        geom=result["geom_interior"] + result["geom_unused"] + result["geom_holes"],
        context="VERTS",
    )
    mesh_builder.to_mesh(mesh)
    mesh_builder.free()
    modifier = mesh_object.modifiers.new(name="decimate", type="DECIMATE")
    modifier.ratio = COLLISION_RATIO
    apply_modifiers(mesh_object)
    return mesh_object


def place_empty(collection, name, location, size):
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "ARROWS"
    empty.empty_display_size = size
    empty.location = Vector(location)
    collection.objects.link(empty)
    return empty


def read_points(factor, center):
    path = SOURCE_DIRECTORY / f"{SOURCE_STEM}_points.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    point = []
    for entry in payload:
        location = (Vector(entry["position"]) - center) * factor
        point.append((entry["name"], location))
    return point


def engine_positions(mesh_object):
    low, high = world_bounds(mesh_object)
    core = ENGINE_CORE_FRACTION * (high.x - low.x)
    aft = min(
        (vertex.co for vertex in mesh_object.data.vertices if abs(vertex.co.x) < core),
        key=lambda co: co.y,
        default=Vector((0.0, low.y, 0.0)),
    )
    lateral = ENGINE_LATERAL_FRACTION * core
    return (
        (-lateral, aft.y, aft.z),
        (lateral, aft.y, aft.z),
    )


def build_connections(collection, mesh_object, point):
    display = SHIP_LENGTH * 0.02
    turret = [item for item in point if item[0] in TURRET_POINT_NAME]
    turret.sort(key=lambda item: (-item[1].y, item[1].x))
    for index, (_, location) in enumerate(turret):
        place_empty(collection, f"con_turret_{index + 1:03d}", location, display)
    dock = [item for item in point if item[0] in DOCK_POINT_NAME]
    for index, (_, location) in enumerate(dock):
        place_empty(collection, f"con_dock_{index + 1:02d}", location, display * 2.0)
    for index, location in enumerate(engine_positions(mesh_object)):
        place_empty(collection, f"con_engine_{index + 1:02d}", location, display)
    return len(turret), len(dock)


def main():
    clear_previous()
    collection = make_collection()
    source = import_source(collection)
    factor, center = normalize(source)
    point = read_points(factor, center)
    lod = [build_lod(collection, source, index) for index in range(len(LOD_RATIO))]
    bpy.data.objects.remove(source, do_unlink=True)
    collision = build_collision(collection, lod[0])
    turret_count, dock_count = build_connections(collection, lod[0], point)
    face = ", ".join(f"lod{index} {len(item.data.polygons)}" for index, item in enumerate(lod))
    print(f"andromeda: {SHIP_LENGTH:.0f} m, scale {factor:.4f}, {face}")
    print(
        f"andromeda: collision {len(collision.data.polygons)} faces, "
        f"{turret_count} turrets, {dock_count} docks"
    )


if "__main__" == __name__:
    main()
