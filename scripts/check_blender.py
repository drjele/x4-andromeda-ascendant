"""Run with Blender 4.2: blender -b --python-exit-code 1 --python scripts/check_blender.py."""

import runpy
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import bpy
from mathutils import Vector

IMPORTER = runpy.run_path(str(Path(__file__).resolve().parents[1] / "andromeda_import.py"))
IMPORTER["clear_scene"]()
mesh = bpy.data.meshes.new("slope")
mesh.from_pydata(
    [(-100, -100, -50), (100, -100, 50), (100, 100, 50), (-100, 100, -50)],
    [],
    [(0, 1, 2), (0, 2, 3)],
)
obj = bpy.data.objects.new("slope", mesh)
bpy.context.scene.collection.objects.link(obj)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
surface = IMPORTER["HullSurface"](mesh)
point, normal = surface.at((20, 0, 0), True, "test_mount")
assert abs(point.z - 10) < 0.001, point
assert (normal - Vector((-0.5, 0, 1)).normalized()).length < 0.001, normal
facing = IMPORTER["longitudinal_facing"](normal).to_quaternion()
assert (facing @ Vector((0, 0, 1)) - normal).length < 0.001
assert (facing @ Vector((0, 1, 0)) - Vector((0, 1, 0))).length < 0.001
for normal_case in (Vector((0.3, 0.4, 1)).normalized(), Vector((0.3, -0.4, -1)).normalized()):
    orientation = IMPORTER["longitudinal_facing"](normal_case).to_quaternion()
    length_axis = orientation @ Vector((0, 1, 0))
    expected = Vector((0, 1, 0)) - normal_case * normal_case.y
    assert length_axis.dot(expected.normalized()) > 0.9999
    assert (orientation @ Vector((0, 0, 1))).dot(normal_case) > 0.9999
try:
    surface.at((10000, 10000, 0), True, "missing")
except ValueError:
    pass
else:
    raise AssertionError("missing surface must not silently remove a mount")
mesh.normals_split_custom_set([tuple(-normal)] * len(mesh.loops))
IMPORTER["repair_winding"](obj)
assert all(p.normal.dot(normal) < 0 for p in mesh.polygons)
IMPORTER["prepare_channels"](obj)
assert set(mesh.color_attributes.keys()) == {"col", "idcode", "paintmodmask"}
assert all(entry.color[0] == 0 for entry in mesh.color_attributes["paintmodmask"].data)
assert all(0.1 < entry.color[0] < 0.3 for entry in mesh.color_attributes["col"].data)
assert mesh.uv_layers.active.name == "uv1"
assert len(IMPORTER["MOUNTS"]) == 54
assert len({mount[0] for mount in IMPORTER["MOUNTS"]}) == 54
print("Blender geometry, ray intersections, orientation and vertex channel checks passed")

if "--" in sys.argv:
    target = Path(sys.argv[sys.argv.index("--") + 1])
    bpy.ops.wm.open_mainfile(filepath=str(target))
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            mesh = obj.data
            for polygon in mesh.polygons:
                normal = sum(
                    (mesh.corner_normals[i].vector for i in polygon.loop_indices), Vector()
                )
                assert polygon.normal.dot(normal) > 0, (obj.name, polygon.index)
            print(f"{obj.name}: {len(mesh.polygons)} faces with coherent normals")
    for name, tags, group, _ in IMPORTER["MOUNTS"]:
        obj = bpy.data.objects.get(name)
        assert obj is not None, name
        assert obj.get("group_name") == group, name
        assert set(obj.get("extratags", "").split()) == set(tags.split()), name
        if "shield" in tags.split():
            rotation = obj.rotation_euler.to_matrix()
            up = rotation @ Vector((0, 0, 1))
            length_axis = rotation @ Vector((0, 1, 0))
            expected = Vector((0, 1, 0)) - up * up.y
            assert length_axis.dot(expected.normalized()) > 0.9999, name
    for name in ("con_weapon_xl_01", "con_weapon_xl_02"):
        obj = bpy.data.objects[name]
        assert obj.rotation_euler.to_matrix() @ Vector((0, 1, 0)) == Vector((0, 1, 0)), name
        assert not obj.get("group_name"), name
        assert "mandatory" not in obj["extratags"].split(), name
    print("Saved scene geometry, longitudinal shields and equipment identities passed")

    dae = ET.parse(target.with_name(target.stem + "_data.dae"))
    namespace = {"c": "http://www.collada.org/2005/11/COLLADASchema"}
    for geometry in dae.findall(".//c:geometry", namespace):
        mesh = geometry.find("c:mesh", namespace)
        sources = {}
        for source in mesh.findall("c:source", namespace):
            values = list(map(float, source.find("c:float_array", namespace).text.split()))
            accessor = source.find("c:technique_common/c:accessor", namespace)
            stride = int(accessor.get("stride", "1"))
            sources["#" + source.get("id")] = [
                values[i : i + stride] for i in range(0, len(values), stride)
            ]
        for vertices in mesh.findall("c:vertices", namespace):
            sources["#" + vertices.get("id")] = sources[
                vertices.find("c:input", namespace).get("source")
            ]
        count = 0
        for triangles in mesh.findall("c:triangles", namespace):
            inputs = {
                entry.get("semantic"): (int(entry.get("offset")), sources[entry.get("source")])
                for entry in triangles.findall("c:input", namespace)
            }
            stride = max(entry[0] for entry in inputs.values()) + 1
            indices = list(map(int, triangles.find("c:p", namespace).text.split()))
            vertex_offset, vertices = inputs["VERTEX"]
            normal_offset, normals = inputs["NORMAL"]
            for i in range(0, len(indices), 3 * stride):
                a, b, c = [
                    Vector(vertices[indices[i + j * stride + vertex_offset]]) for j in range(3)
                ]
                normal = sum(
                    (Vector(normals[indices[i + j * stride + normal_offset]]) for j in range(3)),
                    Vector(),
                )
                assert (b - a).cross(c - a).dot(normal) > 0, (geometry.get("id"), i)
                count += 1
        print(f"DAE {geometry.get('id')}: {count} triangles with coherent winding and normals")
