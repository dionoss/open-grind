from pathlib import Path
import plistlib
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile


SCRIPT = Path(__file__).with_name("verify_ipa.py")


class VerifyIpaTests(unittest.TestCase):
    def fixture(self, path, *, cpu=0x0100000C, signed=False, provisioned=False, traversal=False):
        base = "Payload/Open Grind.app/"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(base + "Info.plist", plistlib.dumps({
                "CFBundleIdentifier": "org.opengrind.app",
                "CFBundleExecutable": "open-grind",
                "CFBundleShortVersionString": "0.1.0",
                "MinimumOSVersion": "16.4",
            }))
            archive.writestr(base + "open-grind", struct.pack("<II", 0xFEEDFACF, cpu) + bytes(24))
            if signed:
                archive.writestr(base + "_CodeSignature/CodeResources", "signed")
            if provisioned:
                archive.writestr(base + "embedded.mobileprovision", "profile")
            if traversal:
                archive.writestr("../escape", "unexpected")

    def run_verify(self, path):
        return subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)

    def test_accepts_unsigned_arm64_phone_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.ipa"
            self.fixture(path)
            result = self.run_verify(path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("org.opengrind.app", result.stdout)

    def test_rejects_simulator_architecture(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.ipa"
            self.fixture(path, cpu=0x01000007)
            self.assertNotEqual(self.run_verify(path).returncode, 0)

    def test_rejects_signed_or_provisioned_payload(self):
        for options in ({"signed": True}, {"provisioned": True}):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "app.ipa"
                self.fixture(path, **options)
                self.assertNotEqual(self.run_verify(path).returncode, 0)

    def test_rejects_archive_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.ipa"
            self.fixture(path, traversal=True)
            self.assertNotEqual(self.run_verify(path).returncode, 0)


if __name__ == "__main__":
    unittest.main()
