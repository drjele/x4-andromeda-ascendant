"""Check local X4 references and shipped DDS/XMF assets without launching the game."""

import argparse
import gzip
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "extension"


def validate(root=ROOT, game=None):
    vanilla_files = None
    if game is not None:
        catalogs = sorted(game.glob("[0-9][0-9].cat"))
        if not catalogs:
            raise ValueError(f"no base game catalogs in {game}")
        vanilla_files = {
            line.rsplit(" ", 3)[0]
            for catalog in catalogs
            for line in catalog.read_text().splitlines()
        }

    errors = []
    trees = {path: ET.parse(path).getroot() for path in root.rglob("*.xml")}
    extension_id = trees[root / "content.xml"].get("id")
    prefix = f"extensions/{extension_id}/"

    def local_path(value):
        normalized = value.replace("\\", "/")
        if not normalized.startswith(prefix):
            raise ValueError(f"unexpected local asset prefix: {value}")
        path = root / normalized[len(prefix) :]
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"asset escapes extension directory: {value}")
        return path

    components = {}
    macros = {}
    for kind, catalog in (("components", components), ("macros", macros)):
        tag = "component" if kind == "components" else "macro"
        for entry in trees[root / "index" / f"{kind}.xml"].iter("entry"):
            name = entry.get("name")
            path = local_path(entry.get("value") + ".xml")
            if name in catalog:
                errors.append(f"duplicate index entry: {name}")
            match = next(
                (
                    node
                    for node in trees.get(path, ET.Element("missing"))
                    if node.tag == tag and node.get("name") == name
                ),
                None,
            )
            if match is None:
                errors.append(f"{name}: indexed definition missing at {path}")
            else:
                catalog[name] = match

    wares = {
        ware.get("id"): ware for ware in trees[root / "libraries/wares.xml"].findall(".//add/ware")
    }
    for name, ware in wares.items():
        ref = ware.find("component")
        if ref is None or ref.get("ref") not in macros:
            errors.append(f"{name}: missing local macro")
    for name, macro in macros.items():
        component = macro.find("component")
        if component is None:
            errors.append(f"{name}: no component")
            continue
        ref = component.get("ref")
        if "_and_" in ref and ref not in components:
            errors.append(f"{name}: missing local component {ref}")
        if ref in components:
            connections = {
                c.get("name") for c in components[ref].findall("./connections/connection")
            }
            for connection in macro.findall("./connections/connection"):
                if connection.get("ref") not in connections:
                    errors.append(f"{name}: missing connection {connection.get('ref')}")

    materials = {
        f"{collection.get('name')}.{material.get('name')}"
        for collection in trees[root / "libraries/material_library.xml"].iter("collection")
        for material in collection.findall("material")
    }
    for name, component in components.items():
        connections = component.findall("./connections/connection")
        names = [c.get("name") for c in connections]
        if len(names) != len(set(names)):
            errors.append(f"{name}: duplicate connection name")
        for connection in connections:
            if (
                component.get("class") == "ship_xl"
                and set(connection.get("tags", "").split())
                & {"medium", "large", "extralarge", "small"}
                and set(connection.get("tags", "").split()) & {"turret", "shield", "engine"}
                and not connection.get("group")
            ):
                errors.append(f"{name}: equipment connection has no group")
        if component.get("class") == "ship_xl":
            groups = {}
            weapon_groups = set()
            for connection in connections:
                tags = set(connection.get("tags", "").split())
                group = connection.get("group")
                if group:
                    groups.setdefault(group, set()).update(tags)
                if "weapon" in tags:
                    weapon_groups.add(group)
            if weapon_groups - {None}:
                errors.append(f"{name}: main weapons must remain ungrouped for the equipment menu")
            for role, custom in (
                ("engine", "engine_and_xl_hidden_01_mk1"),
                ("weapon", "weapon_and_xl_lance_01_mk1"),
            ):
                binding = next(
                    (
                        c
                        for c in components.get(custom, ET.Element("missing")).findall(
                            "./connections/connection"
                        )
                        if "component" in c.get("tags", "").split()
                    ),
                    None,
                )
                if binding is None or "andromeda" not in binding.get("tags", "").split():
                    errors.append(f"{custom}: missing exclusive component binding")
                for connection in connections:
                    tags = set(connection.get("tags", "").split())
                    if role in tags and (
                        "andromeda" not in tags or tags & {"standard", "mandatory"}
                    ):
                        errors.append(
                            f"{connection.get('name')}: incorrect exclusive equipment tags"
                        )
            for group, tags in groups.items():
                if "engine" in tags and "turret" in tags:
                    errors.append(f"{name}: engine and turret share {group}")
                if tags & {"engine", "turret"} and "shield" not in tags:
                    errors.append(f"{name}: no shield in equipment group {group}")
        source = component.find("source")
        if source is None:
            continue
        directory = local_path(source.get("geometry"))
        for part in component.findall(".//parts/part"):
            for lod in part.findall("./lods/lod"):
                asset = directory / f"{part.get('name')}-lod{lod.get('index')}.xmf"
                if not asset.is_file() or asset.stat().st_size < 64:
                    errors.append(f"missing or empty mesh: {asset}")
                for material in lod.findall("./materials/material"):
                    if material.get("ref") not in materials:
                        errors.append(f"unknown local material: {material.get('ref')}")
        for asset in ("part_main-collision.xmf", "part_main-hull.jcs", "part_main-mesh.jcs"):
            path = directory / asset
            if not path.is_file() or path.stat().st_size == 0:
                errors.append(f"missing collision/physics asset: {path}")

    for prop in trees[root / "libraries/material_library.xml"].iter("property"):
        if prop.get("type") == "BitMap":
            value = prop.get("value").replace("\\", "/")
            if value.startswith("assets/") and ".." not in value.split("/"):
                if vanilla_files is not None and value + ".gz" not in vanilla_files:
                    errors.append(f"missing base-game texture: {value}")
            else:
                path = local_path(value + ".gz")
                if not path.is_file():
                    errors.append(f"missing texture: {path}")
    for path in root.glob("assets/textures/**/*.gz"):
        data = gzip.decompress(path.read_bytes())
        if len(data) < 128 or data[:4] != b"DDS " or data[84:88] != b"DXT5":
            errors.append(f"{path}: expected DXT5 DDS")
            continue
        height, width = struct.unpack_from("<II", data, 12)
        mips = struct.unpack_from("<I", data, 28)[0]
        if width == 0 or height == 0 or mips != max(width, height).bit_length():
            errors.append(f"{path}: invalid dimensions or incomplete mip chain")
            continue
        expected = 128 + sum(
            max(1, (max(1, width >> i) + 3) // 4) * max(1, (max(1, height >> i) + 3) // 4) * 16
            for i in range(mips)
        )
        if len(data) != expected:
            errors.append(f"{path}: truncated or unexpected DDS data")

    language = trees[root / "t/0001-l044.xml"]
    text_ids = {
        (page.get("id"), text.get("id"))
        for page in language.iter("page")
        for text in page.findall("t")
    }
    for path, tree in trees.items():
        for node in tree.iter():
            for value in node.attrib.values():
                for page, text in re.findall(r"\{(90001),(\d+)\}", value):
                    if (page, text) not in text_ids:
                        errors.append(f"{path}: missing text {page},{text}")
                if path.parent.name == "md":
                    for ware in re.findall(r"\bware\.([a-zA-Z0-9_]+)", value):
                        if "_and_" in ware and ware not in wares:
                            errors.append(f"{path}: missing blueprint ware {ware}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--game", type=Path, help="also resolve vanilla texture references in base game catalogs"
    )
    option = parser.parse_args()
    try:
        errors = validate(game=option.game)
    except (OSError, ET.ParseError, ValueError, KeyError) as error:
        errors = [str(error)]
    for error in errors:
        print(error, file=sys.stderr)
    if not errors:
        print("Extension references, localization and texture mip chains passed")
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
