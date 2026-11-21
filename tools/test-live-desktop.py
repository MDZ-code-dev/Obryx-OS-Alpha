"""Boot the actual ISO with no writable disk and drive KDE through QEMU."""
import base64
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

import cv2
from PIL import Image, ImageOps

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
def smbios_credential(name, path):
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"type=11,value=io.systemd.credential.binary:{name}={payload}"

vm = subprocess.Popen(
    ["qemu-system-x86_64", "-machine", "q35", "-accel",
     "kvm" if kvm else "tcg", "-cpu", "host" if kvm else "max",
     "-drive", f"if=pflash,format=raw,readonly=on,file={firmware}/OVMF_CODE_4M.fd",
     "-drive", f"if=pflash,format=raw,file={variables}",
     "-smp", "2", "-m", "4096", "-display", "none", "-vga", "std",
     "-device", "qemu-xhci", "-device", "usb-tablet", "-serial", f"file:{artifacts}/guest-serial.log", "-serial", f"file:{artifacts}/journal.log",
     "-smbios", smbios_credential("systemd.extra-unit.onyx-vm-journal.service", journal_unit),
     "-smbios", smbios_credential("systemd.unit-dropin.multi-user.target", wants),
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
        if name in ("home", "apps", "settings"):
            # Read light text on translucent dark panels at a larger scale.
            # Keep the original color capture as the visual test artifact.
            mono = ImageOps.invert(img.convert("L"))
            mono = mono.resize((mono.width * 2, mono.height * 2), Image.Resampling.BICUBIC)
            png = artifacts / "ocr-input.pgm"
            mono.point(lambda value: 0 if value < 110 else 255).save(png)
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
        raise RuntimeError("Could not locate Obryx Home crystal on the dock")
    command("input-send-event", events=[
        {"type": "abs", "data": {"axis": axis, "value": round(value * 32767 / maximum)}}
        for axis, value, maximum in (("x", x, width - 1), ("y", y, height - 1))
    ])
    time.sleep(0.3)
    for down in (True, False):
        command("input-send-event", events=[{"type": "btn", "data": {"button": "left", "down": down}}])
        time.sleep(0.1)
    return x, y, width, height


def type_text(text):
    mapping = {' ': 'spc', '/': 'slash', '.': 'dot', '-': 'minus', '_': 'shift-minus'}
    for char in text:
        keys(mapping.get(char, 'shift-' + char.lower() if char.isupper() else char))


def click_word(word):
    time.sleep(1)
    screen('control-location')
    data = subprocess.check_output(['tesseract', str(artifacts/'control-location.png'),
                                   'stdout', '--psm', '11', 'tsv'], text=True, stderr=subprocess.DEVNULL)
    for line in data.splitlines()[1:]:
        columns = line.split('\t')
        if len(columns) >= 12 and columns[11].strip().casefold() == word.casefold():
            left, top, width, height = map(int, columns[6:10])
            with Image.open(artifacts/'control-location.png') as picture:
                sw, sh = picture.size
            command('input-send-event', events=[
                {'type':'abs','data':{'axis':'x','value':round((left+width/2)*32767/(sw-1))}},
                {'type':'abs','data':{'axis':'y','value':round((top+height/2)*32767/(sh-1))}}])
            for down in (True,False):
                command('input-send-event', events=[{'type':'btn','data':{'button':'left','down':down}}])
            time.sleep(1)
            return
    raise RuntimeError('Could not locate control: '+word)


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
        if not menu_selected and re.search(r"Start\s+Obryx\s+OS", words, re.I):
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
        if re.search(r"GRUB|Start\s+Obryx\s+OS|edit the selected entry", words, re.I):
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
    dock_x, dock_y, screen_width, screen_height = click_home()
    if not wait_for("home", r"(?s)\bFiles\b.*\bBrowser\b.*\bStore\b.*\bTerminal\b", 60):
        raise RuntimeError("Clicking the ONYX dock crystal did not open Home")
    if not wait_for("home", r"Obryx.*0[.,]4", 10):
        raise RuntimeError("Home does not visibly identify ONYX 0.4")
    keys("alt-f4")
    time.sleep(1)
    keys("meta_l")
    if not wait_for("home", r"Pinned.*|All apps", 30):
        raise RuntimeError("Windows key did not open Obryx Home")
    keys("meta_l")
    time.sleep(1)
    if re.search(r"Pinned|All apps", screen("home-closed")):
        raise RuntimeError("Windows key did not close Obryx Home")
    keys("meta_l")
    if not wait_for("home", r"Pinned|All apps", 30):
        raise RuntimeError("Windows key did not reopen Obryx Home")
    keys("ctrl-f")
    if not wait_for("apps", r"Applications|Search installed applications", 30):
        raise RuntimeError("Application search did not open from Home")
    for char in "obryx settings":
        keys("spc" if char == " " else char)
    keys("ret")
    if not wait_for("settings", r"(?s)\bDisplay\b.*\bSound\b.*\bBluetooth\b|Resolution,?\s+scale.*Speakers", 45):
        raise RuntimeError("Obryx Settings did not open from application search")
    click_word('Appearance')
    if not wait_for('appearance', r'Choose wallpaper', 15):
        raise RuntimeError('Appearance has no wallpaper control')
    click_word('Choose')
    time.sleep(1)
    keys('ctrl-l')
    type_text('/usr/share/wallpapers/ONYX/contents/images/1920x1080.png')
    keys('ret')
    if not wait_for('wallpaper', r'Wallpaper applied', 20):
        raise RuntimeError('Wallpaper picker did not apply through Plasma')
    keys('alt-f4')
    # Launch the real terminal command and inspect its output.
    keys('ctrl-alt-t')
    if not wait_for('terminal', r'Konsole|liveuser|onyx', 20):
        raise RuntimeError('Terminal did not open')
    type_text('fastfetch')
    keys('ret')
    if not wait_for('fastfetch', r'(?s)Obryx.*(?:0[.,]4.*Kernel|CPU)', 30):
        raise RuntimeError('Fastfetch did not show ONYX system statistics')
    keys('alt-f4')
    time.sleep(1)
    screen("desktop")
    click_home()
    if not wait_for("home", r"Cyber Mode", 20):
        raise RuntimeError("Home does not expose Cyber Mode")
    click_word("Cyber")
    if not wait_for("cyber", r"(?s)Cyber Mode.*(?:Network interfaces.*Nmap|Wireshark)", 30):
        raise RuntimeError("Cyber Mode dashboard did not launch")
    click_word("interfaces")
    if not wait_for("cyber-network", r"\blo\s+UNKNOWN\b", 25):
        raise RuntimeError("Cyber Mode did not run local interface inspection")
    keys("alt-f4")
    time.sleep(1)
    screen("cyber")
    keys("alt-f4")
    time.sleep(1)
    # Measure the dock, away from its clock, before and after hovering an app.
    command("input-send-event", events=[
        {"type": "abs", "data": {"axis": "x", "value": 1000}},
        {"type": "abs", "data": {"axis": "y", "value": 1000}}])
    time.sleep(1)
    screen("dock-idle")
    command("input-send-event", events=[
        {"type": "abs", "data": {"axis": "x", "value": round((dock_x + 64) * 32767 / (screen_width - 1))}},
        {"type": "abs", "data": {"axis": "y", "value": round(dock_y * 32767 / (screen_height - 1))}}])
    time.sleep(0.4)
    screen("dock-hover")
    idle = cv2.imread(str(artifacts / "dock-idle.png"))
    hover = cv2.imread(str(artifacts / "dock-hover.png"))
    region = (slice(-110, None), slice(dock_x + 24, dock_x + 200))
    difference = cv2.absdiff(idle[region], hover[region])
    changed = (difference.max(axis=2) > 20).sum()
    if changed < 150:
        raise RuntimeError(f"Dock hover did not visibly animate ({changed} pixels)")
    journal_text = (artifacts / "journal.log").read_text(errors="replace")
    if "ONYX_VISUAL_READY version=0.4.0" not in journal_text:
        raise RuntimeError("The live session did not confirm both glass effects and the new layout")
    print(f"ONYX 0.4 UEFI, Home, search, Settings, loaded glass effects and hover passed ({changed} pixels).")
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
