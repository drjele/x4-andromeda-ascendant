import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="andromeda tests ")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        shutil.copytree(ROOT / "lib", self.repo / "lib")
        for name in ("install.sh", "publish.sh"):
            shutil.copy2(ROOT / name, self.repo / name)
        self.source = self.repo / "extension"
        self.source.mkdir()
        (self.source / "content.xml").write_text(
            "<content\n name='test'\n id='andromeda_ascendant'/>\n"
        )
        (self.source / "preview.jpg").write_bytes(b"preview")
        (self.source / "new").write_text("new asset")
        self.game = self.base / "game"
        (self.game / "extensions").mkdir(parents=True)
        self.target = self.game / "extensions/andromeda_ascendant"
        self.target.mkdir()
        (self.target / "old").write_text("old asset")
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.env = dict(
            os.environ, X4_PATH=str(self.game), PATH=str(self.bin) + os.pathsep + os.environ["PATH"]
        )

    def executable(self, name, body):
        path = self.bin / name
        path.write_text("#!/usr/bin/env bash\nset -eu\n" + body + "\n")
        path.chmod(0o755)
        return path

    def run_script(self, name, *arguments):
        return subprocess.run(
            ["bash", str(self.repo / name), *arguments],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=20,
        )

    def assert_restored(self):
        self.assertEqual((self.target / "old").read_text(), "old asset")
        self.assertFalse((self.target / "new").exists())
        self.assertEqual(list(self.game.glob(".andromeda_ascendant.*")), [])

    def mock_workshop(self, body):
        self.executable("uname", "echo MINGW64_NT")
        tool = self.executable("WorkshopTool.exe", body)
        self.env["X_TOOLS_PATH"] = str(tool)

    def test_install_and_uninstall(self):
        result = self.run_script("install.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.target / "new").is_file())
        self.assertFalse((self.target / "old").exists())
        self.assertEqual(self.run_script("install.sh", "--uninstall").returncode, 0)
        self.assertFalse(self.target.exists())

    def test_unknown_argument_does_not_install(self):
        self.assertEqual(self.run_script("install.sh", "--wrong").returncode, 2)
        self.assert_restored()

    def test_failed_copy_preserves_previous_install(self):
        self.executable("cp", "exit 7")
        self.assertEqual(self.run_script("install.sh").returncode, 7)
        self.assert_restored()

    def test_failed_replacement_restores_previous_install(self):
        real_mv = shutil.which("mv")
        self.executable(
            "mv", f'if [[ "${{2:-}}" == */new ]]; then exit 8; fi\nexec "{real_mv}" "$@"'
        )
        self.assertEqual(self.run_script("install.sh").returncode, 8)
        self.assert_restored()

    def test_interrupted_copy_preserves_previous_install(self):
        self.executable("cp", 'kill -TERM "$PPID"\nexit 143')
        self.assertEqual(self.run_script("install.sh").returncode, 143)
        self.assert_restored()

    def test_rejects_traversal_and_symlink(self):
        (self.source / "content.xml").write_text('<content id="../../escape"/>')
        self.assertNotEqual(self.run_script("install.sh").returncode, 0)
        self.assert_restored()
        (self.source / "content.xml").write_text('<content id="andromeda_ascendant"/>')
        shutil.rmtree(self.target)
        self.target.symlink_to(self.source, target_is_directory=True)
        self.assertNotEqual(self.run_script("install.sh").returncode, 0)
        self.assertTrue((self.source / "new").exists())

    def test_failed_publish_restores_exact_previous_install(self):
        self.mock_workshop("exit 9")
        self.assertEqual(self.run_script("publish.sh", "publish").returncode, 9)
        self.assert_restored()
        self.assertFalse((self.repo / "steam/workshop-id").exists())

    def test_successful_publish_records_id_and_restores(self):
        self.mock_workshop('printf \'<content id="ws_123456"/>\\n\' > "$3/content.xml"')
        result = self.run_script("publish.sh", "publish")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.repo / "steam/workshop-id").read_text(), "123456\n")
        self.assert_restored()
        self.assertIn("andromeda_ascendant", (self.source / "content.xml").read_text())

    def test_missing_workshop_result_is_failure(self):
        self.mock_workshop("exit 0")
        self.assertNotEqual(self.run_script("publish.sh", "publish").returncode, 0)
        self.assert_restored()

    def test_update_id_must_not_be_sanitized(self):
        (self.repo / "steam").mkdir()
        (self.repo / "steam/workshop-id").write_text("bad123id")
        self.mock_workshop("exit 0")
        self.assertNotEqual(self.run_script("publish.sh", "update", "test").returncode, 0)
        self.assert_restored()

    def test_publish_without_previous_install_removes_stage(self):
        shutil.rmtree(self.target)
        self.mock_workshop("exit 9")
        self.assertEqual(self.run_script("publish.sh", "publish").returncode, 9)
        self.assertFalse(self.target.exists())

    def test_successful_update_preserves_id_and_literal_note(self):
        (self.repo / "steam").mkdir()
        (self.repo / "steam/workshop-id").write_text("123456\n")
        self.mock_workshop('printf "%s" "$6" > "$X4_PATH/note"')
        note = "literal `command` and $(command)\nsecond line"
        result = self.run_script("publish.sh", "update", note)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.game / "note").read_text(), note)
        self.assertEqual((self.repo / "steam/workshop-id").read_text(), "123456\n")
        self.assert_restored()

    def test_update_must_not_change_workshop_id(self):
        (self.repo / "steam").mkdir()
        (self.repo / "steam/workshop-id").write_text("123456\n")
        self.mock_workshop('printf \'<content id="ws_999"/>\\n\' > "$3/content.xml"')
        self.assertNotEqual(self.run_script("publish.sh", "update", "test").returncode, 0)
        self.assertEqual((self.repo / "steam/workshop-id").read_text(), "123456\n")
        self.assert_restored()
