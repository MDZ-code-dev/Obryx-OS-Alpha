#!/usr/bin/env python3
"""Integrate ONYX before Fedora's terminal exit, and add image dependencies."""
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

PACKAGES = ("dbus-tools", "plasma-discover", "flatpak")


def prepare(upstream: Path, source: Path):
    config = upstream / "config.sh"
    script = config.read_text()
    marker = "# BEGIN ONYX FINAL CONFIGURATION"
    if marker in script:
        raise ValueError("Already customized: use a fresh upstream checkout")
    terminal = re.search(r"(?m)^exit 0\s*\Z", script)
    if not terminal:
        raise ValueError("Fedora config.sh no longer ends with exit 0; review upstream")
    hook = (source / "build/onyx-config-hook.sh").read_text()
    script = (script[:terminal.start()] + marker + "\n" + hook
              + "\n# END ONYX FINAL CONFIGURATION\nexit 0\n")
    config.write_text(script)
    recipe = upstream / "Fedora.kiwi"
    tree = ET.parse(recipe)
    packages = ET.SubElement(tree.getroot(), "packages", {
        "type": "image", "profiles": "KDE-Desktop-Live"})
    for name in PACKAGES:
        ET.SubElement(packages, "package", {"name": name})
    tree.write(recipe, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    prepare(Path(sys.argv[1]), Path(__file__).resolve().parents[1])
