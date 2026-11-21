#!/usr/bin/env python3
"""ONYX 0.3 static source checks. Not a substitute for boot tests."""
from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
overlay = root / "overlay/root"
checks = {
    "plasma layout": overlay / "usr/share/onyx-os/plasma-layout.js",
    "ONYX splash": overlay / "usr/share/plasma/look-and-feel/org.onyx.desktop/contents/splash/Splash.qml",
    "splash metadata": overlay / "usr/share/plasma/look-and-feel/org.onyx.desktop/metadata.json",
    "session initializer": overlay / "usr/local/bin/onyx-desktop-setup",
    "session autostart": overlay / "etc/xdg/autostart/onyx-desktop-setup.desktop",
    "ONYX store": overlay / "usr/share/applications/onyx-store.desktop",
    "ONYX settings": overlay / "usr/share/applications/onyx-settings.desktop",
    "branding hook": root / "build/onyx-config-hook.sh",
}
errors = []
for label, path in checks.items():
    if not path.is_file() or not path.stat().st_size:
        errors.append(f"Missing {label}: {path.relative_to(root)}")

if not errors:
    try:
        metadata = json.loads(checks["splash metadata"].read_text())
        assert metadata["KPlugin"]["Id"] == "org.onyx.desktop"
    except (ValueError, KeyError, AssertionError) as exc:
        errors.append(f"Invalid splash metadata: {exc}")
    layout = checks["plasma layout"].read_text()
    for widget in ("org.obryx.home", "onyx-home.desktop", "per.nonobeam.paneldock", "org.kde.plasma.systemtray"):
        if widget not in layout:
            errors.append(f"Missing functional Plasma widget: {widget}")
    script = checks["session initializer"].read_text()
    if "dbus-send" not in script or "--print-reply" not in script:
        errors.append("Session script must wait for a D-Bus method reply")
    if "desktop-0.4-applied" not in script:
        errors.append("Session script needs a first-run completion marker")
    hook = checks["branding hook"].read_text()
    if "Theme=org.onyx.desktop" not in hook:
        errors.append("ONYX splash not configured in image hook")
    for label in ("ONYX store", "ONYX settings"):
        desktop = checks[label].read_text()
        if "[Desktop Entry]" not in desktop or "Exec=" not in desktop:
            errors.append(f"{label} is not a valid desktop entry")

launcher = overlay / "usr/share/plasma/plasmoids/org.obryx.home/metadata.json"
try:
    metadata = json.loads(launcher.read_text())
    assert "org.kde.plasma.launchermenu" in metadata["X-Plasma-Provides"]
    assert metadata["KPlugin"]["Id"] == "org.obryx.home"
except (OSError, ValueError, KeyError, AssertionError) as exc:
    errors.append(f"Home must register as a Plasma launcher: {exc}")
for asset in ("crystal.svg", "onyx-logo.svg"):
    ET.parse(overlay / "usr/share/onyx-os" / asset)

if errors:
    print("ONYX 0.3 source preflight FAILED:", *errors, sep="\n - ", file=sys.stderr)
    sys.exit(1)
print(f"ONYX 0.3 source preflight passed ({len(checks)} assets).")
print("NOTE: Static checks cannot verify that the ISO boots or Plasma accepts its layout.")
