"""Check one unprovisioned arm64 iPhone app, without executing its code."""

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
            header = binary.read(32)
            if len(header) != 32:
                raise ValueError("Truncated Mach-O header")
            magic, cpu, _, filetype, count, size, _, _ = struct.unpack("<IIIIIIII", header)
            if (magic, cpu, filetype) != (0xFEEDFACF, 0x0100000C, 2):
                raise ValueError("Expected a thin arm64 Mach-O executable")
            if not 0 < count <= 4096 or not 0 < size <= 16 * 1024 * 1024:
                raise ValueError("Invalid Mach-O load-command bounds")
            commands = binary.read(size)
        if len(commands) != size:
            raise ValueError("Truncated Mach-O load commands")
        offset = 0
        platforms = []
        for _ in range(count):
            if offset + 8 > size:
                raise ValueError("Missing Mach-O load command")
            command, length = struct.unpack_from("<II", commands, offset)
            if length < 8 or offset + length > size:
                raise ValueError("Invalid Mach-O load-command length")
            if command == 0x32:  # LC_BUILD_VERSION: platform 2 is iOS, 7 is iOS Simulator.
                if length < 24:
                    raise ValueError("Truncated Mach-O build version")
                platforms.append(struct.unpack_from("<I", commands, offset + 8)[0])
            offset += length
        if offset != size or platforms != [2]:
            raise ValueError("Expected a physical iOS platform load command")
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
        "platform": "ios-device",
        "provisioning_profile_present": False,
        "app_signature_resources_present": False,
        "embedded_adhoc_signature_assessed": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ipa", type=Path)
    print(json.dumps(verify(parser.parse_args().ipa), indent=2))
