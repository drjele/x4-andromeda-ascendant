"""Extract the four original twin-barrel assemblies and export a working X4 turret."""

import argparse
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

NAME = "turret_and_l_twin_01_mk1"
TAGS = "turret large andromeda hittable combat"
# Original OBJ coordinates, ordered aft port/starboard then ventral port/starboard.
STATIONS = (
    (-193.55751, -174.1044, 38.68175),
    (193.55751, -174.1044, 38.68175),
    (-82.81758, 22.11699, -110.09495),
    (82.81758, 22.11699, -110.09495),
)


def islands(mesh):
    parent = list(range(len(mesh.vertices)))

    def root(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(a, b):
        parent[root(a)] = root(b)

    welded = {}
    for vertex in mesh.vertices:
        key = tuple(round(c, 3) for c in vertex.co)
        if key in welded:
            union(vertex.index, welded[key])
        else:
            welded[key] = vertex.index
    for polygon in mesh.polygons:
        for index in polygon.vertices[1:]:
            union(polygon.vertices[0], index)
    groups = {}
    for vertex in mesh.vertices:
        groups.setdefault(root(vertex.index), set()).add(vertex.index)
    return list(groups.values())


def assemblies(mesh):
    groups = islands(mesh)
    result = []
    for station in STATIONS:
        point = Vector(station)
        nearby = []
        for indices in groups:
            if len(indices) not in (21, 33, 58):
                continue
            low = Vector(tuple(min(mesh.vertices[i].co[a] for i in indices) for a in range(3)))
            high = Vector(tuple(max(mesh.vertices[i].co[a] for i in indices) for a in range(3)))
            if ((low + high) * 0.5 - point).length < 45:
                nearby.append((indices, low, high))
        if sorted(len(item[0]) for item in nearby) != [21, 33, 33, 58, 58]:
            raise ValueError(f"Cannot identify complete original twin turret at {station}")
        barrels = [item for item in nearby if len(item[0]) == 58]
        centers = [(low + high) * 0.5 for _, low, high in barrels]
        right = (centers[1] - centers[0]).normalized()
        forward = Vector((0, 1, 0))
        up = right.cross(forward).normalized()
        if up.z * station[2] < 0:
            right = -right
            up = -up
        frame = Matrix((right, forward, up)).transposed()
        pivot = (centers[0] + centers[1]) * 0.5
        pivot.y = sum(item[1].y for item in barrels) * 0.5
        result.append((nearby, pivot, frame))
    return result


def remove_from_hull(source):
    """Identify before normalization; remove whole islands, never slice hull faces."""
    found = assemblies(source.data)
    selected = set().union(*(item[0] for assembly, _, _ in found for item in assembly))
    bm = bmesh.new()
    bm.from_mesh(source.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in selected], context="VERTS")
    bm.to_mesh(source.data)
    bm.free()
    source.data.update()
    print(f"andromeda: separated four original turrets ({len(selected)} source vertices)")
    return [(pivot, frame) for _, pivot, frame in found]


def build(target, source_directory, export):
    import andromeda_import as hull

    hull.SOURCE_DIRECTORY = source_directory
    hull.clear_scene()
    source = hull.import_source()
    hull.repair_winding(source)
    found = assemblies(source.data)
    # Starboard dorsal assembly is the common model; the other mounts supply its roll.
    assembly, pivot, frame = found[1]
    factor = hull.SHIP_LENGTH / (
        max(v.co.y for v in source.data.vertices) - min(v.co.y for v in source.data.vertices)
    )
    inverse = frame.transposed()
    parts = {}
    for name, count in (("part_socket", 21), ("part_yaw", 33), ("part_pitch", 58)):
        indices = set().union(*(ids for ids, _, _ in assembly if len(ids) == count))
        vertices = sorted(indices)
        remap = {index: i for i, index in enumerate(vertices)}
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(
            [inverse @ (source.data.vertices[i].co - pivot) * factor for i in vertices],
            [],
            [
                tuple(remap[i] for i in p.vertices)
                for p in source.data.polygons
                if set(p.vertices) <= indices
            ],
        )
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        hull.prepare_channels(obj)
        hull.correct_shading(obj)
        parts[name] = obj
    parts["part_yaw"].parent = parts["part_socket"]
    parts["part_pitch"].parent = parts["part_yaw"]
    for name, axis in (("part_yaw", "z"), ("part_pitch", "x")):
        obj = parts[name]
        for group, definitions in bpy.propertyGroupLayouts.items():
            if any(item["name"] == "iklink" for item in definitions):
                getattr(obj, group).iklink = True
        constraint = obj.constraints.new("LIMIT_ROTATION")
        constraint.owner_space = "LOCAL"
        constraint.use_limit_x = constraint.use_limit_y = constraint.use_limit_z = True
        if axis == "z":
            constraint.use_limit_z = False
        else:
            constraint.min_x = math.radians(-5)
            constraint.max_x = math.radians(85)
    for index, (ids, low, high) in enumerate(item for item in assembly if len(item[0]) == 58):
        muzzle = (low + high) * 0.5
        muzzle.y = high.y + 0.25
        connection = hull.add_connection(
            f"con_laser_{index + 1:02d}", "laser", inverse @ (muzzle - pivot) * factor
        )
        connection.parent = parts["part_pitch"]
    hull.add_connection("con_turret", "component turret large andromeda combat", (0, 0, 0))
    hull.add_connection("con_aimtarget", "aimtarget", (0, 0, 0))
    bpy.data.objects.remove(source, do_unlink=True)
    bpy.context.scene.classAttr = "turret"
    target.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    if export:
        bpy.ops.ego_tools.export_data(write_xml=True)
    print("andromeda: exported twin turret with socket, yaw, pitch and two muzzle connections")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--source", type=Path, default=Path.home() / "x4mod/source")
    parser.add_argument("--export", action="store_true")
    options = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    build(options.target, options.source, options.export)
