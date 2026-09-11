"""Package a converted Andromeda hull while retaining the shipped connection contract."""

import argparse
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "ship_and_xl_cruiser_01"


def connections(tree):
    return {
        node.get("name"): (frozenset(node.get("tags", "").split()), node.get("group"))
        for node in tree.findall(".//connections/connection")
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("converted", type=Path)
    parser.add_argument(
        "--component",
        type=Path,
        required=True,
        help="fresh component XML from the Blender exporter",
    )
    option = parser.parse_args()
    destination = ROOT / "extension/assets/units/size_xl"
    source_xml = option.component
    tree = ET.parse(source_xml)
    previous = ET.parse(destination / f"{NAME}.xml")
    old_connections, new_connections = connections(previous), connections(tree)
    corrected_groups = {
        "con_engine_01": "group_engine_left",
        "con_engine_02": "group_engine_right",
        "con_weapon_xl_01": None,
        "con_weapon_xl_02": None,
    }
    corrected_tags = {
        "con_engine_01": frozenset("engine extralarge andromeda".split()),
        "con_engine_02": frozenset("engine extralarge andromeda".split()),
        "con_weapon_xl_01": frozenset("combat extralarge andromeda weapon".split()),
        "con_weapon_xl_02": frozenset("combat extralarge andromeda weapon".split()),
    }
    for name, (tags, group) in old_connections.items():
        expected = (corrected_tags.get(name, tags), corrected_groups.get(name, group))
        if new_connections.get(name) != expected:
            raise ValueError(f"export changes existing connection contract: {name}")
    additions = new_connections.keys() - old_connections.keys()
    allowed = {f"con_shieldgen_m_{i:03d}" for i in range(1, 15)}
    integrated = {f"con_turret_integrated_{i:02d}" for i in range(1, 5)}
    allowed |= integrated
    if not additions <= allowed or any(
        new_connections[name][0]
        != (
            frozenset("turret large andromeda hittable combat".split())
            if name in integrated
            else frozenset(("medium", "shield", "hittable", "standard"))
        )
        for name in additions
    ):
        raise ValueError("unexpected new equipment connections")
    component = tree.find("component")
    if component is None or component.get("name") != NAME or component.get("class") != "ship_xl":
        raise ValueError("unexpected ship component")
    geometry_name = f"{NAME}_data"
    geometry = option.converted / geometry_name
    files = [f"part_main-lod{i}.xmf" for i in range(4)] + ["part_main_wreck-lod0.xmf"]
    files += [
        f"{part}-{suffix}"
        for part in ("part_main", "part_main_wreck")
        for suffix in ("collision.xmf", "hull.jcs", "mesh.jcs")
    ]
    for name in files:
        path = geometry / name
        if not path.is_file() or path.stat().st_size < 16:
            raise ValueError(f"missing or empty converted asset: {path}")
    animation = option.converted / f"{geometry_name}.ani"
    if not animation.is_file() or animation.stat().st_size == 0:
        raise ValueError("missing converted animation")
    component.find("source").set(
        "geometry", f"extensions\\andromeda_ascendant\\assets\\units\\size_xl\\{geometry_name}"
    )
    for name in files:
        shutil.copyfile(geometry / name, destination / geometry_name / name)
    shutil.copyfile(animation, destination / animation.name)
    ET.indent(tree, space="    ")
    tree.write(destination / f"{NAME}.xml", encoding="utf-8", xml_declaration=True)
    with (destination / f"{NAME}.xml").open("a") as output:
        output.write("\n")
    print(
        f"Packaged {len(files)} mesh/physics files; existing connection names retained; equipment compatibility and groups validated"
    )


if __name__ == "__main__":
    main()
