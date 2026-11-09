#!/usr/bin/env bash
# ONYX OS 0.3 Alpha - Fedora 45 KDE Live image build.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORK="${ONYX_WORKDIR:-$ROOT/work}"
OUT="${ONYX_OUTPUT:-$ROOT/output}"
UPSTREAM="https://forge.fedoraproject.org/releng/kiwi-descriptions.git"
if [[ "${1:-}" == "--check" ]]; then
  for file in "$ROOT/overlay/root/usr/share/onyx-os/onyx-logo.svg"     "$ROOT/overlay/root/usr/share/wallpapers/ONYX/contents/images/1920x1080.svg"     "$ROOT/overlay/root/usr/local/bin/onyx-first-login"     "$ROOT/build/onyx-config-hook.sh"     "$ROOT/overlay/root/etc/xdg/autostart/onyx-first-login.desktop"; do
    [[ -s "$file" ]] || { echo "Missing required ONYX file: $file"; exit 1; }
  done
  bash -n "$ROOT/build/onyx-config-hook.sh" "$ROOT/overlay/root/usr/local/bin/onyx-first-login" "$ROOT/overlay/root/usr/local/bin/onyx-desktop-setup"
  python3 "$ROOT/tools/validate-onyx-source.py"
  [[ -s "$ROOT/overlay/root/usr/share/onyx-os/plasma-layout.js" ]] || exit 1
  [[ -s "$ROOT/overlay/root/usr/share/plasma/look-and-feel/org.onyx.desktop/contents/splash/Splash.qml" ]] || exit 1
  echo "ONYX 0.3 source files and scripts verified (not a boot test)."
  exit 0
fi
[[ "$(uname -m)" == "x86_64" ]] || { echo "x86_64 build host required"; exit 1; }
[[ -f /etc/fedora-release ]] || { echo "Run this on Fedora Linux."; exit 1; }
(( EUID == 0 )) || { echo "Run with sudo/root."; exit 1; }
dnf -y install kiwi kiwi-systemdeps distribution-gpg-keys git python3 file librsvg2-tools google-noto-sans-fonts
mkdir -p "$WORK" "$OUT"
if [[ ! -d "$WORK/upstream/.git" ]]; then
  git clone --depth 1 --branch f45 "$UPSTREAM" "$WORK/upstream"
else
  git -C "$WORK/upstream" fetch --depth 1 origin f45
  git -C "$WORK/upstream" checkout --force FETCH_HEAD
fi
[[ -f "$WORK/upstream/Fedora.kiwi" && -f "$WORK/upstream/kiwi-build" && -f "$WORK/upstream/config.sh" ]] || {
 echo "Fedora KIWI image descriptions missing."; exit 1;
}
SVG="$ROOT/overlay/root/usr/share/wallpapers/ONYX/contents/images/1920x1080.svg"
PNG="$ROOT/overlay/root/usr/share/wallpapers/ONYX/contents/images/1920x1080.png"
rsvg-convert -w 1920 -h 1080 -o "$PNG" "$SVG"
[[ -s "$PNG" ]] || { echo "ONYX wallpaper conversion failed"; exit 1; }
file "$PNG" | grep -q 'PNG image data' || { echo "Generated wallpaper is not PNG"; exit 1; }
chmod +x "$ROOT/overlay/root/usr/local/bin/onyx-desktop-setup"
chmod +x "$ROOT/overlay/root/usr/local/bin/onyx-first-login"
mkdir -p "$WORK/upstream/root"
cp -a "$ROOT/overlay/root/." "$WORK/upstream/root/"
# Fedora's config.sh runs after KIWI applies the overlay. Apply our default
# settings last, and fail the image if ONYX files were not included.
printf '\n\n# ONYX OS final system-level branding check and defaults\n' >> "$WORK/upstream/config.sh"
cat "$ROOT/build/onyx-config-hook.sh" >> "$WORK/upstream/config.sh"
echo "ONYX branding hook added to Fedora KIWI config.sh"
cd "$WORK/upstream"
./kiwi-build --kiwi-file=Fedora.kiwi --image-type=iso --image-profile=KDE-Desktop-Live --output-dir="$OUT"
IMAGE_DIRS=()
for dir in "$OUT" "$ROOT/output-build" "$WORK/upstream/output-build"; do
  [[ -d "$dir" ]] && IMAGE_DIRS+=("$dir")
done
mapfile -t ISOS < <(find "${IMAGE_DIRS[@]}" -maxdepth 2 -type f -name '*.iso' -print | sort -u)
[[ "${#ISOS[@]}" -eq 1 ]] || { echo "Expected one ISO, found ${#ISOS[@]}"; exit 1; }
TARGET="$OUT/ONYX-OS-0.3-Alpha-x86_64.iso"
[[ "${ISOS[0]}" == "$TARGET" ]] || mv -- "${ISOS[0]}" "$TARGET"
[[ -s "$TARGET" ]] || { echo "Empty ISO"; exit 1; }
(cd "$OUT" && sha256sum "$(basename "$TARGET")" > "$(basename "$TARGET").sha256")
ls -lh "$TARGET" "$TARGET.sha256"
echo "ONYX 0.3 ISO created. Boot and desktop must still be verified on real hardware."
