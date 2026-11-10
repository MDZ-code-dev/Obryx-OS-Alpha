"""Boot the actual ISO with no writable disk and drive KDE through QEMU."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

import cv2
from PIL import Image

artifacts = Path("vm-test").resolve()
artifacts.mkdir(exist_ok=True)
iso = Path(sys.argv[1]).resolve(strict=True)
kvm = os.access("/dev/kvm", os.R_OK | os.W_OK)
firmware = Path("/usr/share/OVMF")
variables = artifacts / "OVMF_VARS.fd"
shutil.copyfile(firmware / "OVMF_VARS_4M.fd", variables)
# Pass diagnostic units through the VM firmware only. The published ISO
# gets no debug login, privileged agent or extra startup service.
journal_unit = artifacts / "journal.service"
journal_unit.write_text(
    "[Unit]\nDescription=Capture diskless VM journal\n"
    "ConditionPathExists=!/etc/initrd-release\nAfter=systemd-journald.service\n"
    "[Service]\nExecStart=/usr/bin/journalctl -b -f --no-pager -o short-monotonic\n"
    "StandardOutput=tty\nTTYPath=/dev/ttyS1\n"
)
wants = artifacts / "journal-wants.conf"
wants.write_text("[Unit]\nWants=onyx-vm-journal.service\n")
cred = "name=opt/io.systemd.credentials/"
vm = subprocess.Popen(
    ["qemu-system-x86_64", "-machine", "q35", "-accel",
     "kvm" if kvm else "tcg", "-cpu", "host" if kvm else "max",
     "-drive", f"if=pflash,format=raw,readonly=on,file={firmware}/OVMF_CODE_4M.fd",
     "-drive", f"if=pflash,format=raw,file={variables}",
     "-smp", "2", "-m", "4096", "-display", "none", "-vga", "std",
     "-device", "qemu-xhci", "-device", "usb-tablet", "-serial", f"file:{artifacts}/guest-serial.log", "-serial", f"file:{artifacts}/journal.log",
     "-fw_cfg", f"{cred}systemd.extra-unit.onyx-vm-journal.service,file={journal_unit}",
     "-fw_cfg", f"{cred}systemd.unit-dropin.multi-user.target,file={wants}",
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


def click_home():
    # Match the installed crystal on the dock, accounting for panel scaling.
    shot = cv2.imread(str(artifacts / "desktop.png"), cv2.IMREAD_GRAYSCALE)
    height, width = shot.shape
    region = shot[-95:, :width // 2]
    icon = cv2.imread("overlay/root/usr/share/onyx-os/icons/crystal.png", cv2.IMREAD_UNCHANGED)
    best = (-1, 0, 0)
    for size in range(18, 67, 2):
        tile = cv2.resize(icon, (round(size * 72 / 84), size), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(tile, cv2.COLOR_BGRA2GRAY)
        alpha = tile[:, :, 3] / 255
        template = (gray * alpha + 30 * (1 - alpha)).astype("uint8")
        matches = cv2.matchTemplate(region, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, (left, top) = cv2.minMaxLoc(matches)
        if score > best[0]:
            best = (score, left + tile.shape[1] // 2, height - 95 + top + size // 2)
    score, x, y = best
    print(f"Dock crystal match {score:.3f} at {x},{y}", flush=True)
    if score < 0.75:
        raise RuntimeError("Could not locate ONYX Home crystal on the dock")
    command("input-send-event", events=[
        {"type": "abs", "data": {"axis": axis, "value": round(value * 32767 / maximum)}}
        for axis, value, maximum in (("x", x, width - 1), ("y", y, height - 1))
    ])
    time.sleep(0.3)
    for down in (True, False):
        command("input-send-event", events=[{"type": "btn", "data": {"button": "left", "down": down}}])
        time.sleep(0.1)


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
    # GRUB treats the E in Super+E as "edit boot entry". Let the default
    # entry boot, or explicitly select it when the ONYX menu is visible.
    start = time.monotonic()
    menu_selected = False
    last_boot_frame = -1
    while time.monotonic() - start < 180:
        elapsed = int(time.monotonic() - start)
        name = f"boot-{elapsed:03d}"
        words = screen(name)
        if not menu_selected and re.search(r"Start\s+ONYX\s+OS", words, re.I):
            keys("ret")
            menu_selected = True
        if re.search(r"\b\d{1,2}:\d{2}\b", words) and not re.search(
            r"GRUB|firmware|boot manager", words, re.I
        ):
            break
        last_boot_frame = elapsed
        time.sleep(2)
    else:
        print(f"Boot observation ended at {last_boot_frame}s", flush=True)

    # Keep early boot captures, and never send desktop keys into GRUB.
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        words = screen("pre-shortcut")
        if re.search(r"GRUB|Start\s+ONYX\s+OS|edit the selected entry", words, re.I):
            raise RuntimeError("VM is still at the bootloader before the desktop shortcut")
        keys("meta_l-e")
        if wait_for("file-manager", r"\bDolphin\b|\bTrash\b", 12):
            break
    else:
        raise RuntimeError("The live desktop did not open Dolphin with Super+E")
    keys("alt-f4")
    time.sleep(1)
    desktop_text = screen("desktop")
    if re.search(r"Welcome Center|Install to Hard Drive", desktop_text, re.I):
        raise RuntimeError("Upstream installer welcome is covering the live desktop")
    # Activate the installed panel applet. Building the GTK window directly
    # would miss a broken Plasma widget or panel layout.
    click_home()
    if not wait_for("home", r"Quick\s+launch", 60):
        raise RuntimeError("Clicking the ONYX dock crystal did not open Home")
    keys("ctrl-f")
    for char in "onyx settings":
        keys("spc" if char == " " else char)
    keys("ret")
    if not wait_for("settings", r"Resolution,?\s+scale|Speakers,?\s+microphones", 30):
        raise RuntimeError("ONYX Settings did not open from application search")
    print("UEFI boot, Dolphin, ONYX Home, app search and Settings passed.")
except RuntimeError:
    journal = artifacts / "journal.log"
    if journal.is_file():
        lines = journal.read_text(errors="replace").splitlines()
        for line in lines:
            if re.search(r"onyx|shell\.py|traceback|error|gtk|gdk|python|qml|plasmashell", line, re.I):
                print(line, flush=True)
    raise
finally:
    vm.terminate()
    vm.wait(timeout=20)
