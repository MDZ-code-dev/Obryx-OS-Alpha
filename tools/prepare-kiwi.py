#!/usr/bin/env python3
"""Integrate ONYX before Fedora's terminal exit, and add image dependencies."""
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

PACKAGES = ("dbus-tools", "plasma-discover", "flatpak", "anaconda-live")


def customize_boot_menu(template: Path):
    menu = template.read_text()
    entry = re.compile(r'(?m)^menuentry "Start \$\{title\}"[^\n]*\{\n(?:[^\n]*\n)*?^\}')
    matches = list(entry.finditer(menu))
    if len(matches) != 1:
        raise ValueError("Expected one Fedora live start entry in the x86 GRUB template")
    original = matches[0].group()
    start = original.replace('Start ${title}', 'Start ONYX OS', 1)
    install, count = re.subn(r'(?m)^(\s*linux(?:efi)?[ \t]+[^\n]+)$',
                             r'\1 onyx.install=1', start.replace('Start ONYX OS', 'Install ONYX OS', 1))
    if count != 1 or '${boot_options}' not in start:
        raise ValueError("Unexpected live kernel command in the Fedora GRUB template")
    menu = menu.replace(original, start + "\n" + install)
    menu, count = re.subn(r'(?m)^set default=.*$', 'set default="0"', menu)
    if count != 1:
        raise ValueError("Expected one GRUB default entry setting")
    template.write_text(menu)


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
    customize_boot_menu(upstream / "grub-x86.cfg.iso-template")
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
