"""Validate the live entry authored into the ONYX 0.4 image."""
from pathlib import Path
import re
import sys

menu = Path(sys.argv[1]).read_text()
entries = re.findall(r"^menuentry\s+[\"']([^\"']+)[\"'][^\n]*\n(.*?)^}", menu, re.M | re.S)
assert entries and entries[0][0] == "Start ONYX OS 0.4", "Missing versioned live entry"
assert "onyx.install=1" not in menu, "Live testing build must boot the desktop"
assert re.search(r'^set default="0"$', menu, re.M), "Live desktop must be default"
assert re.search(r"^\s*linux(?:efi)?\s+", entries[0][1], re.M), "Missing live kernel"
print("Verified ONYX OS 0.4 live boot menu.")
