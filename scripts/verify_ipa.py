"""Check that an IPA contains one unsigned arm64 iPhone app."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import plistlib
import struct
import zipfile


def verify(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate IPA entries")
        if any(PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts for n in names):
            raise ValueError("Unsafe IPA entry path")
        plists = [n for n in names if len(PurePosixPath(n).parts) == 3
                  and n.startswith("Payload/") and n.endswith(".app/Info.plist")]
        if len(plists) != 1:
            raise ValueError("Expected exactly one application Info.plist")
        info = plistlib.loads(archive.read(plists[0]))
        base = plists[0].removesuffix("Info.plist")
        executable = info["CFBundleExecutable"]
        if "/" in executable or executable in (".", ".."):
            raise ValueError("Invalid application executable name")
        with archive.open(base + executable) as binary:
            header = binary.read(8)
        if len(header) != 8 or struct.unpack("<II", header) != (0xFEEDFACF, 0x0100000C):
            raise ValueError("Expected a thin arm64 Mach-O executable")
        if base + "embedded.mobileprovision" in names or any(n.startswith(base + "_CodeSignature/") for n in names):
            raise ValueError("IPA contains signing or provisioning data")
        if info["CFBundleIdentifier"] != "org.opengrind.app":
            raise ValueError("Unexpected app bundle identifier")
    return {
        "filename": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bundle_identifier": info["CFBundleIdentifier"],
        "version": info["CFBundleShortVersionString"],
        "minimum_ios": info.get("MinimumOSVersion"),
        "architecture": "arm64",
        "signed": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ipa", type=Path)
    print(json.dumps(verify(parser.parse_args().ipa), indent=2))
