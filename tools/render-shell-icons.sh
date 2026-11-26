#!/usr/bin/env bash
set -euo pipefail
art="$(cd -- "$(dirname -- "$0")/../overlay/root/usr/share/onyx-os" && pwd)"
for source in "$art"/icons/*.svg; do
  rsvg-convert -w 80 -h 80 -o "${source%.svg}.png" "$source"
done
rsvg-convert -w 72 -h 84 -o "$art/icons/crystal.png" "$art/crystal.svg"
