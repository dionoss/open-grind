"""Prepare only the iOS configuration for an unsigned personal build."""

import argparse
import json
from pathlib import Path
import re


def prepare(root: Path) -> None:
    tauri = root / "src-tauri"
    version = json.loads((tauri / "tauri.conf.json").read_text())["version"]
    match = re.fullmatch(r"(\d+\.\d+\.\d+)(?:[-+].*)?", version)
    if not match:
        raise ValueError(f"Cannot convert {version!r} to an Apple version")
    path = tauri / "tauri.ios.conf.json"
    config = json.loads(path.read_text())
    config["version"] = match.group(1)
    # cargo-mobile2 rejects an empty team even when --no-sign skips signing.
    # This placeholder is not an Apple account or a signing authorization.
    config.setdefault("bundle", {}).setdefault("iOS", {})["developmentTeam"] = "0000000000"
    changes = {}
    for path in (tauri / "gen/apple").rglob("*"):
        if path.is_file() and (path.name == "project.yml" or path.suffix == ".pbxproj"):
            text = path.read_text()
            text = re.sub(
                r'(\b(?:DEVELOPMENT_TEAM|DevelopmentTeam)\s*[=:]\s*)(?:"[A-Z0-9]{10}"|[A-Z0-9]{10})',
                r'\g<1>"0000000000"',
                text,
            )
            changes[path] = text
    (tauri / "tauri.ios.conf.json").write_text(json.dumps(config, indent=2) + "\n")
    for path, text in changes.items():
        path.write_text(text)
    print(json.dumps({"version": config["version"], "signing": "disabled"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    prepare(parser.parse_args().source)
