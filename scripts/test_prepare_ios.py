import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("prepare_ios.py")


class PrepareIosTests(unittest.TestCase):
    def fixture(self, root, version="0.1.0-rc.1-dev"):
        tauri = root / "src-tauri"
        apple = tauri / "gen/apple/open-grind.xcodeproj"
        apple.mkdir(parents=True)
        (tauri / "tauri.conf.json").write_text(json.dumps({"version": version}))
        (tauri / "tauri.ios.conf.json").write_text(json.dumps({
            "identifier": "org.opengrind.app",
            "bundle": {"iOS": {"developmentTeam": "ABCDEFGHIJ", "minimumSystemVersion": "16.4"}},
        }))
        (apple / "project.pbxproj").write_text('DEVELOPMENT_TEAM = ABCDEFGHIJ;\nDevelopmentTeam = "ABCDEFGHIJ";\n')
        (apple.parent / "project.yml").write_text("DEVELOPMENT_TEAM: ABCDEFGHIJ\n")
        return tauri

    def run_prepare(self, root):
        return subprocess.run([sys.executable, str(SCRIPT), str(root)], capture_output=True, text=True)

    def test_unsigned_configuration_removes_author_team_and_normalizes_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tauri = self.fixture(root)
            result = self.run_prepare(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            config = json.loads((tauri / "tauri.ios.conf.json").read_text())
            self.assertEqual(config["version"], "0.1.0")
            self.assertEqual(config["bundle"]["iOS"]["developmentTeam"], "0000000000")
            self.assertEqual(config["bundle"]["iOS"]["minimumSystemVersion"], "16.4")
            for path in (tauri / "gen/apple").rglob("*"):
                if path.is_file():
                    self.assertNotIn("ABCDEFGHIJ", path.read_text())

    def test_invalid_version_fails_without_changing_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tauri = self.fixture(root, "not-a-version")
            before = (tauri / "tauri.ios.conf.json").read_bytes()
            self.assertNotEqual(self.run_prepare(root).returncode, 0)
            self.assertEqual((tauri / "tauri.ios.conf.json").read_bytes(), before)

    def test_second_run_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tauri = self.fixture(root)
            first = self.run_prepare(root)
            self.assertEqual(first.returncode, 0, first.stderr)
            before = {p: p.read_bytes() for p in tauri.rglob("*") if p.is_file()}
            second = self.run_prepare(root)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual({p: p.read_bytes() for p in before}, before)


if __name__ == "__main__":
    unittest.main()
