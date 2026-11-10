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
     "-serial", "file:vm-test/guest.log", "-drive", "file=qa.img,format=raw,if=virtio,readonly=on",
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
    if not wait_for("welcome", r"Welcome (to|Center)|Install to Hard Drive", 280):
        raise RuntimeError("No live session welcome screen")
    time.sleep(8)
    keys("alt-f4")
    time.sleep(3)
    keys("alt-f2")
    time.sleep(3)
    for c in "konsole":
        keys(c)
    keys("ret")
    if not wait_for("console", r"konsole|liveuser|bash", 25):
        keys("ctrl-alt-t")
        time.sleep(6)
    for line in ["sudo mount -L ONYXQA /mnt", "sudo bash /mnt/check", "gtk-launch onyx-home"]:
        for c in line:
            if c.isupper():
                keys("shift-" + c.lower())
            else:
                keys({" ":"spc","/":"slash","-":"minus"}.get(c, c))
        keys("ret")
        time.sleep(4)
    screen("home")
    print(Path("vm-test/guest.log").read_text(errors="replace")[-32000:])
    if not wait_for("direct-home", r"Quick\s+launch", 30):
        raise RuntimeError("Home did not launch directly")
    keys("esc")
    time.sleep(1)
    keys("meta_l")
    if not wait_for("meta-home", r"Quick\s+launch", 12):
        raise RuntimeError("Meta did not open ONYX Home")
finally:
    vm.terminate()
    vm.wait(timeout=20)
