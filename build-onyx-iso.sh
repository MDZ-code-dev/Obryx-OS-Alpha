#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORK="${ONYX_WORKDIR:-$ROOT/work}"
OUT="${ONYX_OUTPUT:-$ROOT/output}"
UPSTREAM="https://forge.fedoraproject.org/releng/kiwi-descriptions.git"
if [[ "${1:-}" == "--check" ]]; then
  for file in "$ROOT/overlay/root/usr/share/onyx-os/onyx-logo.svg" "$ROOT/overlay/root/usr/share/wallpapers/ONYX/contents/images/1920x1080.svg" "$ROOT/overlay/root/usr/local/bin/onyx-first-login"; do
    [[ -s "$file" ]] || { echo "Missing: $file"; exit 1; }
  done
  echo "ONYX source files found. This does not verify a bootable ISO."
  exit 0
fi
[[ "$(uname -m)" == "x86_64" ]] || { echo "x86_64 host required"; exit 1; }
[[ -f /etc/fedora-release ]] || { echo "Run on Fedora Linux."; exit 1; }
if (( EUID != 0 )); then echo "Run with sudo/root."; exit 1; fi
dnf -y install kiwi kiwi-systemdeps distribution-gpg-keys git python3
mkdir -p "$WORK" "$OUT"
if [[ ! -d "$WORK/upstream/.git" ]]; then
  git clone --depth 1 --branch f45 "$UPSTREAM" "$WORK/upstream"
else
  git -C "$WORK/upstream" fetch --depth 1 origin f45
  git -C "$WORK/upstream" checkout --force FETCH_HEAD
fi
[[ -f "$WORK/upstream/Fedora.kiwi" && -f "$WORK/upstream/kiwi-build" ]] || { echo "Fedora KIWI files not found"; exit 1; }
mkdir -p "$WORK/upstream/root"
cp -a "$ROOT/overlay/root/." "$WORK/upstream/root/"
cd "$WORK/upstream"
./kiwi-build --kiwi-file=Fedora.kiwi --image-type=iso --image-profile=KDE-Desktop-Live --output-dir="$OUT"
# The upstream Fedora kiwi-build wrapper writes its finished ISO to
# ${project}/output-build even if --output-dir has been passed to kiwi-build.
# Inspect both locations instead of assuming the Fedora build failed.
IMAGE_DIRS=()
for dir in "$OUT" "$ROOT/output-build" "$WORK/upstream/output-build"; do
  if [[ -d "$dir" ]]; then IMAGE_DIRS+=("$dir"); fi
done
mapfile -t ISOS < <(find "${IMAGE_DIRS[@]}" -maxdepth 2 -type f -name '*.iso' -print | sort -u)
if [[ "${#ISOS[@]}" -ne 1 ]]; then
  echo "Expected exactly one ISO; found ${#ISOS[@]}"
  printf 'Searched: %s\n' "${IMAGE_DIRS[@]}"
  printf 'Candidates: %s\n' "${ISOS[@]:-none}"
  exit 1
fi
TARGET="$OUT/ONYX-OS-0.1-Alpha-x86_64.iso"
if [[ "${ISOS[0]}" != "$TARGET" ]]; then mv -- "${ISOS[0]}" "$TARGET"; fi
[[ -s "$TARGET" ]] || { echo "Empty ISO: $TARGET"; exit 1; }
(cd "$OUT" && sha256sum "$(basename "$TARGET")" > "$(basename "$TARGET").sha256")
ls -lh "$TARGET" "$TARGET.sha256"
echo "ISO produced at $TARGET; boot-testing remains required."
