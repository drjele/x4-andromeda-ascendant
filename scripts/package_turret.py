"""Package the converted integrated twin turret, checking its articulation contract."""

import argparse
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "turret_and_l_twin_01_mk1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("converted", type=Path)
    parser.add_argument("--component", type=Path, required=True)
    options = parser.parse_args()
    tree = ET.parse(options.component)
    component = tree.find("component")
    if component.get("name") != NAME or component.get("class") != "turret":
        raise ValueError("unexpected turret component")
    for part, parent, axis in (
        ("part_yaw", "part_socket", "rotation_y"),
        ("part_pitch", "part_yaw", "rotation_x"),
    ):
        connection = component.find(f"./connections/connection[@name='ConnectionFor{part}']")
        if (
            connection.get("parent") != parent
            or "iklink" not in connection.get("tags", "").split()
            or connection.find(f"./restrictions/restriction[@type='{axis}']") is None
        ):
            raise ValueError(f"missing turret articulation: {part}")
    for index in (1, 2):
        connection = component.find(f"./connections/connection[@name='con_laser_{index:02d}']")
        if (
            connection.get("parent") != "part_pitch"
            or "laser" not in connection.get("tags", "").split()
        ):
            raise ValueError("muzzle does not follow the barrels")
    data_name = NAME + "_data"
    paths = [
        Path(data_name) / f"{part}-{suffix}"
        for part in ("part_socket", "part_yaw", "part_pitch")
        for suffix in ("lod0.xmf", "collision.xmf", "hull.jcs", "mesh.jcs")
    ]
    paths.append(Path(data_name + ".ani"))
    for relative in paths:
        path = options.converted / relative
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"missing converted asset: {path}")
    destination = ROOT / "extension/assets/props/weaponsystems/energy"
    component.find("source").set(
        "geometry",
        f"extensions\\andromeda_ascendant\\assets\\props\\weaponsystems\\energy\\{data_name}",
    )
    for relative in paths:
        (destination / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(options.converted / relative, destination / relative)
    ET.indent(tree, space="    ")
    tree.write(destination / f"{NAME}.xml", encoding="utf-8", xml_declaration=True)
    with (destination / f"{NAME}.xml").open("a") as output:
        output.write("\n")
    print("Packaged twin turret: three parts, two aiming joints, two moving muzzles")


if __name__ == "__main__":
    main()
