import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_extension", ROOT / "scripts/validate_extension.py"
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ExtensionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "extension"
        shutil.copytree(ROOT / "extension", self.root)

    def test_shipped_references(self):
        self.assertEqual(VALIDATOR.validate(self.root), [])

    def test_missing_indexed_macro(self):
        path = self.root / "assets/props/engines/macros/engine_and_xl_hidden_01_mk1_macro.xml"
        path.unlink()
        self.assertTrue(
            any("indexed definition missing" in error for error in VALIDATOR.validate(self.root))
        )

    def test_missing_collision(self):
        (
            self.root / "assets/units/size_xl/ship_and_xl_cruiser_01_data/part_main-collision.xmf"
        ).unlink()
        self.assertTrue(
            any("missing collision" in error for error in VALIDATOR.validate(self.root))
        )

    def test_missing_texture(self):
        import xml.etree.ElementTree as ET

        path = self.root / "libraries/material_library.xml"
        tree = ET.parse(path)
        tree.find(".//property[@name='diffuse_map']").set(
            "value", "extensions/andromeda_ascendant/missing"
        )
        tree.write(path)
        self.assertTrue(any("missing texture" in error for error in VALIDATOR.validate(self.root)))

    def test_grouped_weapons_and_standard_engines_are_rejected(self):
        import xml.etree.ElementTree as ET

        path = self.root / "assets/units/size_xl/ship_and_xl_cruiser_01.xml"
        tree = ET.parse(path)
        tree.find(".//connection[@name='con_weapon_xl_01']").set("group", "hidden_weapons")
        tree.find(".//connection[@name='con_engine_01']").set("tags", "engine extralarge standard")
        tree.write(path)
        errors = VALIDATOR.validate(self.root)
        self.assertTrue(any("ungrouped" in error for error in errors))
        self.assertTrue(any("exclusive equipment" in error for error in errors))

    def test_ravager_weapon_has_its_own_selectable_component(self):
        import xml.etree.ElementTree as ET

        path = (
            self.root
            / "assets/props/weaponsystems/capital/macros/weapon_and_xl_lance_01_mk1_macro.xml"
        )
        tree = ET.parse(path)
        self.assertEqual(tree.find(".//component").get("ref"), "weapon_and_xl_lance_01_mk1")
        self.assertEqual(tree.find(".//bullet").get("class"), "bullet_kha_xl_beam_01_mk1_macro")
        component = ET.parse(path.parent.parent / "weapon_and_xl_lance_01_mk1.xml")
        binding = component.find(".//connection[@name='con_weapon_01']")
        self.assertIn("andromeda", binding.get("tags").split())
        self.assertNotIn("mandatory", binding.get("tags").split())
        self.assertIsNotNone(component.find(".//connection[@tags='laser']"))

    def test_unprotected_or_mixed_equipment_groups(self):
        import xml.etree.ElementTree as ET

        path = self.root / "assets/units/size_xl/ship_and_xl_cruiser_01.xml"
        tree = ET.parse(path)
        for connection in tree.findall(".//connections/connection"):
            if connection.get("name") == "con_engine_01":
                connection.set("group", "group_front_up_left")
            if connection.get("name") == "con_turret_001":
                connection.set("group", "unprotected")
        tree.write(path)
        errors = VALIDATOR.validate(self.root)
        self.assertTrue(any("engine and turret share" in error for error in errors))
        self.assertTrue(any("no shield" in error for error in errors))

    def test_integrated_turrets_are_four_exclusive_slots(self):
        import xml.etree.ElementTree as ET

        tree = ET.parse(self.root / "assets/units/size_xl/ship_and_xl_cruiser_01.xml")
        mounts = [
            c
            for c in tree.findall(".//connections/connection")
            if c.get("name", "").startswith("con_turret_integrated_")
        ]
        self.assertEqual(len(mounts), 4)
        for mount in mounts:
            self.assertEqual(
                set(mount.get("tags").split()),
                {"turret", "large", "andromeda", "hittable", "combat"},
            )

    def test_broken_turret_joint_is_rejected(self):
        import xml.etree.ElementTree as ET

        path = self.root / "assets/props/weaponsystems/energy/turret_and_l_twin_01_mk1.xml"
        tree = ET.parse(path)
        tree.find(".//connection[@name='ConnectionForpart_yaw']").set("tags", "part")
        tree.write(path)
        self.assertTrue(
            any("broken aiming joint" in error for error in VALIDATOR.validate(self.root))
        )

    def test_disconnected_turret_muzzle_is_rejected(self):
        import xml.etree.ElementTree as ET

        path = self.root / "assets/props/weaponsystems/energy/turret_and_l_twin_01_mk1.xml"
        tree = ET.parse(path)
        tree.find(".//connection[@name='con_laser_01']").set("parent", "part_socket")
        tree.write(path)
        self.assertTrue(
            any("muzzle must follow" in error for error in VALIDATOR.validate(self.root))
        )
