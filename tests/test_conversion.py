import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "soase_import", Path(__file__).resolve().parents[1] / "soase_import.py"
)
CONVERTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONVERTER)


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.position = [CONVERTER.to_target_axes(v) for v in ((0, 0, 0), (1, 0, 0), (0, 1, 0))]
        self.normal = [CONVERTER.to_target_axes((0, 0, 1))] * 3
        self.uv = [(0, 0), (1, 0), (0, 1)]

    def test_axis_transform_preserves_winding_and_every_material(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mesh.obj"
            CONVERTER.write_object(
                path, "mesh", self.position, self.normal, self.uv, [(0, 1, 2, 0), (0, 1, 2, 1)], 2
            )
            faces = [line for line in path.read_text().splitlines() if line.startswith("f ")]
            self.assertEqual(faces, ["f 1/1/1 2/2/2 3/3/3"] * 2)
            self.assertIn("usemtl mesh_1", path.read_text())

    def test_rejects_bad_geometry_before_writing(self):
        for triangles in (
            [(0, 1, 3, 0)],
            [(-1, 1, 2, 0)],
            [(0, 1, 2, 2)],
            [(0, 0, 1, 0)],
            [(0, 2, 1, 0)],
        ):
            with self.subTest(triangles=triangles), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "bad.obj"
                with self.assertRaises(ValueError):
                    CONVERTER.write_object(
                        path, "bad", self.position, self.normal, self.uv, triangles, 1
                    )
                self.assertFalse(path.exists())

    def test_conversion_parses_text_and_flips_uv(self):
        text = 'TXT\nMeshData\n\tMaterial\n\t\tDiffuseTextureFileName "test.dds"\n'
        for position, uv in (
            ((0, 0, 0), (0.2, 0.3)),
            ((1, 0, 0), (0.4, 0.5)),
            ((0, 1, 0), (0.6, 0.7)),
        ):
            text += f"\tVertex\n\t\tPosition [{' '.join(map(str, position))}]\n\t\tNormal [0 0 1]\n\t\tU0 {uv[0]}\n\t\tV0 {uv[1]}\n"
        text += "\tTriangle\n\t\tiVertex0 0\n\t\tiVertex1 1\n\t\tiVertex2 2\n\t\tiMaterial 0\n"
        text += '\tPoint\n\t\tDataString "Hangar"\n\t\tPosition [1 2 3]\n'
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "sample.mesh"
            source.write_text(text)
            output = Path(directory) / "out"
            CONVERTER.convert(source, output)
            self.assertIn("vt 0.200000 0.700000", (output / "sample.obj").read_text())
            point = json.loads((output / "sample_points.json").read_text())[0]
            self.assertEqual(point["position"], [-1, 3, 2])

    def test_binary_mesh_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.mesh"
            source.write_bytes(b"BIN\0")
            with self.assertRaisesRegex(ValueError, "text-format"):
                CONVERTER.convert(source, Path(directory) / "out")
            self.assertFalse((Path(directory) / "out").exists())

    def test_hardpoint_basis_change_preserves_identity(self):
        identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        self.assertEqual(CONVERTER.to_target_orientation(identity), identity)
        source_rotation = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
        target_rotation = CONVERTER.to_target_orientation(source_rotation)
        source_vector = (1, 2, 3)
        rotated = [sum(row[i] * source_vector[i] for i in range(3)) for row in source_rotation]
        target_vector = CONVERTER.to_target_axes(source_vector)
        result = [sum(row[i] * target_vector[i] for i in range(3)) for row in target_rotation]
        self.assertEqual(result, list(CONVERTER.to_target_axes(rotated)))
