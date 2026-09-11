"""Convert Sins of a Solar Empire text meshes to OBJ for the Andromeda pipeline."""

import argparse
import json
import math
import sys
from pathlib import Path

TEXT_MAGIC = "TXT"
SOURCE_FORWARD_SIGN = 1.0
UV_CHANNEL = ("U0", "V0")


def parse_vector(value):
    return tuple(float(part) for part in value.strip().strip("[]").split())


def parse_nodes(line, start, depth):
    nodes = []
    index = start
    total = len(line)
    while index < total:
        current = line[index]
        if "" == current.strip():
            index += 1
            continue
        current_depth = len(current) - len(current.lstrip("\t"))
        if current_depth < depth:
            break
        head = current.strip()
        key, _, value = head.partition(" ")
        children, index = parse_nodes(line, index + 1, depth + 1)
        nodes.append((key, value, children))
    return nodes, index


def collect(nodes, key):
    return [node for node in nodes if key == node[0]]


def field(nodes, key, fallback=""):
    for node in nodes:
        if key == node[0]:
            return node[1]
    return fallback


def read_mesh(path):
    line = path.read_bytes().decode("latin-1").replace("\r\n", "\n").split("\n")
    if 0 == len(line) or TEXT_MAGIC != line[0].strip():
        raise ValueError(
            f"{path.name}: not a text-format Sins mesh, convert it with ConvertX first"
        )
    nodes, _ = parse_nodes(line, 1, 0)
    root = collect(nodes, "MeshData")
    if 0 == len(root):
        raise ValueError(f"{path.name}: no MeshData block")
    return root[0][2]


def read_materials(body):
    material = []
    for _, _, children in collect(body, "Material"):
        material.append(
            {
                "diffuse": field(children, "DiffuseTextureFileName").strip('"'),
                "illumination": field(children, "SelfIlluminationTextureFileName").strip('"'),
                "normal": field(children, "NormalTextureFileName").strip('"'),
                "team_color": field(children, "TeamColorTextureFileName").strip('"'),
                "glossiness": float(field(children, "Glossiness", "0")),
            }
        )
    return material


def read_vertices(body):
    position = []
    normal = []
    texture_coordinate = []
    for _, _, children in collect(body, "Vertex"):
        position.append(parse_vector(field(children, "Position")))
        normal.append(parse_vector(field(children, "Normal")))
        u = float(field(children, UV_CHANNEL[0], "0"))
        v = float(field(children, UV_CHANNEL[1], "0"))
        texture_coordinate.append((u, 1.0 - v))
    return position, normal, texture_coordinate


def read_triangles(body):
    triangle = []
    for _, _, children in collect(body, "Triangle"):
        triangle.append(
            (
                int(field(children, "iVertex0", "0")),
                int(field(children, "iVertex1", "0")),
                int(field(children, "iVertex2", "0")),
                int(field(children, "iMaterial", "0")),
            )
        )
    return triangle


def read_points(body):
    point = []
    for _, _, children in collect(body, "Point"):
        rows = []
        for node in collect(children, "Orientation"):
            rows = [parse_vector(row[1]) for row in node[2]]
        point.append(
            {
                "name": field(children, "DataString").strip('"'),
                "position": parse_vector(field(children, "Position")),
                "orientation": rows,
            }
        )
    return point


def to_target_axes(vector):
    x, y, z = vector
    return (-x, SOURCE_FORWARD_SIGN * z, y)


def extents(position):
    low = [min(value[axis] for value in position) for axis in range(3)]
    high = [max(value[axis] for value in position) for axis in range(3)]
    return low, high


def write_material_library(path, material, stem):
    line = [f"# converted from {stem}.mesh"]
    for index, entry in enumerate(material):
        line.append(f"newmtl {stem}_{index}")
        line.append("Ka 1.000 1.000 1.000")
        line.append("Kd 1.000 1.000 1.000")
        line.append(f"Ns {entry['glossiness']:.3f}")
        if "" != entry["diffuse"]:
            line.append(f"map_Kd {entry['diffuse']}")
        if "" != entry["illumination"]:
            line.append(f"map_Ke {entry['illumination']}")
        if "" != entry["normal"]:
            line.append(f"map_Bump {entry['normal']}")
        line.append("")
    path.write_text("\n".join(line) + "\n", encoding="utf-8")


def validate_geometry(position, normal, texture_coordinate, triangle, material_count):
    if not position or not triangle or material_count < 1:
        raise ValueError("mesh must contain vertices, triangles and materials")
    if len(position) != len(normal) or len(position) != len(texture_coordinate):
        raise ValueError("vertex, normal and UV counts differ")
    for values, width in ((position, 3), (normal, 3), (texture_coordinate, 2)):
        if any(len(v) != width or not all(math.isfinite(x) for x in v) for v in values):
            raise ValueError("invalid vertex, normal or UV coordinates")
    for index, (first, second, third, material) in enumerate(triangle):
        if any(v < 0 or v >= len(position) for v in (first, second, third)):
            raise ValueError(f"triangle {index}: vertex index out of range")
        if material < 0 or material >= material_count:
            raise ValueError(f"triangle {index}: material index out of range")
        a, b, c = (position[v] for v in (first, second, third))
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        if sum(x * x for x in cross) <= 1e-20:
            raise ValueError(f"triangle {index}: degenerate face")
        average = [sum(normal[j][i] for j in (first, second, third)) for i in range(3)]
        if sum(cross[i] * average[i] for i in range(3)) <= 0:
            raise ValueError(f"triangle {index}: winding disagrees with vertex normals")


def write_object(path, stem, position, normal, texture_coordinate, triangle, material_count):
    validate_geometry(position, normal, texture_coordinate, triangle, material_count)
    line = [f"# converted from {stem}.mesh", f"mtllib {stem}.mtl", f"o {stem}"]
    for value in position:
        line.append(f"v {value[0]:.6f} {value[1]:.6f} {value[2]:.6f}")
    for value in texture_coordinate:
        line.append(f"vt {value[0]:.6f} {value[1]:.6f}")
    for value in normal:
        line.append(f"vn {value[0]:.6f} {value[1]:.6f} {value[2]:.6f}")
    for material_index in range(material_count):
        face = [entry for entry in triangle if material_index == entry[3]]
        if 0 == len(face):
            continue
        line.append(f"usemtl {stem}_{material_index}")
        for first, second, third in ((entry[0], entry[1], entry[2]) for entry in face):
            corner = " ".join(
                f"{value + 1}/{value + 1}/{value + 1}" for value in (first, second, third)
            )
            line.append(f"f {corner}")
    path.write_text("\n".join(line) + "\n", encoding="utf-8")


def to_target_orientation(rows):
    if not rows:
        return []
    if len(rows) != 3 or any(len(row) != 3 for row in rows):
        raise ValueError("hardpoint orientation must be a 3 by 3 matrix")
    basis = ((-1, 0, 0), (0, 0, SOURCE_FORWARD_SIGN), (0, 1, 0))
    return [
        [
            sum(basis[i][k] * rows[k][m] * basis[j][m] for k in range(3) for m in range(3))
            for j in range(3)
        ]
        for i in range(3)
    ]


def write_points(path, point):
    payload = [
        {
            "name": entry["name"],
            "position": list(to_target_axes(entry["position"])),
            "orientation": to_target_orientation(entry["orientation"]),
        }
        for entry in point
    ]
    path.write_text(json.dumps(payload, indent=4) + "\n", encoding="utf-8")


def convert(source, destination):
    body = read_mesh(source)
    material = read_materials(body)
    raw_position, raw_normal, texture_coordinate = read_vertices(body)
    triangle = read_triangles(body)
    point = read_points(body)
    position = [to_target_axes(value) for value in raw_position]
    normal = [to_target_axes(value) for value in raw_normal]
    stem = source.stem
    validate_geometry(position, normal, texture_coordinate, triangle, len(material))
    destination.mkdir(parents=True, exist_ok=True)
    write_material_library(destination / f"{stem}.mtl", material, stem)
    write_object(
        destination / f"{stem}.obj",
        stem,
        position,
        normal,
        texture_coordinate,
        triangle,
        len(material),
    )
    write_points(destination / f"{stem}_points.json", point)
    low, high = extents(position)
    print(f"{stem}: {len(position)} vertices, {len(triangle)} triangles, {len(material)} materials")
    print(f"{stem}: {len(point)} points, {', '.join(sorted({entry['name'] for entry in point}))}")
    print(
        f"{stem}: extents x {high[0] - low[0]:.1f}, y {high[1] - low[1]:.1f}, "
        f"z {high[2] - low[2]:.1f}"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, nargs="+", help="text-format .mesh files")
    parser.add_argument("-o", "--output", type=Path, required=True, help="destination directory")
    option = parser.parse_args()
    for source in option.source:
        convert(source, option.output)
    return 0


if "__main__" == __name__:
    sys.exit(main())
