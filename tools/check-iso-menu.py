"""Verify that the rendered ISO has distinct live and install boot paths."""
from pathlib import Path
import re
import sys

menu = Path(sys.argv[1]).read_text()
entries = re.findall(r'^menuentry\s+["\']([^"\']+)["\'][^\n]*\n(.*?)^}', menu, re.M | re.S)
for title, install in (("Start ONYX OS", False), ("Install ONYX OS", True)):
    bodies = [body for name, body in entries if name == title]
    if len(bodies) != 1:
        sys.exit(f"Expected one GRUB entry named {title}")
    kernels = re.findall(r"^\s*linux(?:efi)?\s+(.+)$", bodies[0], re.M)
    if len(kernels) != 1 or ("onyx.install=1" in kernels[0].split()) != install:
        sys.exit(f"Invalid kernel options for {title}")
if entries[0][0] != "Start ONYX OS" or not re.search(r'^set default="0"$', menu, re.M):
    sys.exit("Start ONYX OS must be the default")
print("Verified live and interactive installer entries in the GRUB menu.")
