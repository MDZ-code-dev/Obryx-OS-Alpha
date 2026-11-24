#!/usr/bin/env python3
"""Integrate ONYX before Fedora's terminal exit, and add image dependencies."""
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

PACKAGES = ("git", "kate", "gcc", "gcc-c++", "make", "cmake", "ninja-build", "gdb", "python3-pip", "python3-virtualenv", "python3-pyserial", "ccache", "dfu-util", "libusb1", "flex", "bison", "gperf", "nmap", "wireshark", "bind-utils", "openssl", "podman", "fastfetch", "dbus-tools", "plasma-discover", "flatpak", "anaconda-live", "gtk3", "python3-gobject", "plasma5support", "plymouth-theme-spinner")


def customize_boot_menu(template: Path):
    menu = template.read_text()
    entry = re.compile(r'(?m)^menuentry "Start \$\{title\}"[^\n]*\{\n(?:[^\n]*\n)*?^\}')
    matches = list(entry.finditer(menu))
    if len(matches) != 1:
        raise ValueError("Expected one Fedora live start entry in the x86 GRUB template")
    original = matches[0].group()
    start = original.replace('Start ${title}', 'Start Obryx OS', 1)
    start = start.replace("Start Obryx OS", "Start Obryx OS 0.4")
    menu = menu.replace(original, start).replace("${title}", "Obryx OS 0.4")
    menu, count = re.subn(r'(?m)^set default=.*$', 'set default="0"', menu)
    if count != 1:
        raise ValueError("Expected one GRUB default entry setting")
    # Fedora's live menu waits up to a minute. Boot the default entry after 3 seconds.
    menu, count = re.subn(r'(?m)^set timeout=.*$', 'set timeout=3', menu)
    if count == 0:
        menu = menu.replace('set default="0"', 'set default="0"\nset timeout=3', 1)
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
