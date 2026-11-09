"""Boot the actual ISO with no writable disk and drive KDE through QEMU."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from PIL import Image

artifacts = Path("vm-test").resolve()
artifacts.mkdir(exist_ok=True)
iso = Path(sys.argv[1]).resolve(strict=True)
kvm = os.access("/dev/kvm", os.R_OK | os.W_OK)
firmware = Path("/usr/share/OVMF")
variables = artifacts / "OVMF_VARS.fd"
shutil.copyfile(firmware / "OVMF_VARS_4M.fd", variables)
vm = subprocess.Popen(
    ["qemu-system-x86_64", "-machine", "q35", "-accel",
     "kvm" if kvm else "tcg", "-cpu", "host" if kvm else "max",
     "-drive", f"if=pflash,format=raw,readonly=on,file={firmware}/OVMF_CODE_4M.fd",
     "-drive", f"if=pflash,format=raw,file={variables}",
     "-smp", "2", "-m", "4096", "-display", "none", "-vga", "std",
     "-nic", "none", "-boot", "d", "-cdrom", str(iso), "-qmp", "stdio"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
)


def receive():
    line = vm.stdout.readline()
    if not line:
        raise RuntimeError("VM exited before the desktop test completed")
    return json.loads(line)


def command(name, **args):
    vm.stdin.write(json.dumps({"execute": name, "arguments": args}) + "\n")
    vm.stdin.flush()
    while True:
        reply = receive()
        if "error" in reply:
            raise RuntimeError(reply["error"])
        if "return" in reply:
            return


def keys(combo):
    command("human-monitor-command", **{"command-line": "sendkey " + combo})
    time.sleep(0.18)


def screen(name):
    ppm = artifacts / "current.ppm"
    command("screendump", filename=str(ppm))
    png = artifacts / (name + ".png")
    with Image.open(ppm) as img:
        img.save(png)
    return subprocess.check_output(
        ["tesseract", str(png), "stdout", "--psm", "11"],
        stderr=subprocess.DEVNULL, text=True,
    )


def wait_for(name, pattern, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if re.search(pattern, screen(name), flags=re.I | re.M):
            return True
        time.sleep(2)
    return False


try:
    receive()
    command("qmp_capabilities")
    # Wait for a working Plasma shortcut. Retry while the live system starts.
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        keys("meta_l-e")
        if wait_for("file-manager", r"\bDolphin\b|\bTrash\b", 12):
            break
    else:
        raise RuntimeError("The live desktop did not open Dolphin with Super+E")
    keys("alt-f4")
    time.sleep(1)
    screen("desktop")
    # Activate the installed panel applet. Building the GTK window directly
    # would miss a broken Plasma widget or panel layout.
    keys("meta_l")
    if not wait_for("home", r"Quick\s+launch", 20):
        keys("alt-f1")
        if not wait_for("home", r"Quick\s+launch", 15):
            raise RuntimeError("The ONYX panel launcher did not open Home")
    keys("ctrl-f")
    for char in "onyx settings":
        keys("spc" if char == " " else char)
    keys("ret")
    if not wait_for("settings", r"Resolution,?\s+scale|Speakers,?\s+microphones", 30):
        raise RuntimeError("ONYX Settings did not open from application search")
    print("UEFI boot, Dolphin, ONYX Home, app search and Settings passed.")
finally:
    vm.terminate()
    vm.wait(timeout=20)
