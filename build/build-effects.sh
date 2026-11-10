#!/usr/bin/env bash
# Compile pinned open-source effects against the same Fedora runtime as the ISO.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="${ONYX_WORKDIR:-$ROOT/work}/effects"
DEST="$ROOT/overlay/root"
dnf -y install cmake gcc-c++ git extra-cmake-modules kwin-devel \
  kf6-kconfigwidgets-devel libepoxy-devel kf6-kcmutils-devel kf6-ki18n-devel \
  qt6-qtbase-private-devel qt6-qttools-devel wayland-devel libdrm-devel \
  kf6-kwindowsystem-devel kf6-knotifications-devel kf6-kio-devel \
  kf6-kcrash-devel kf6-kguiaddons-devel kf6-kglobalaccel-devel kdecoration-devel
mkdir -p "$CACHE"
build_effect() {
  local name="$1" url="$2" revision="$3"
  shift 3
  local source="$CACHE/$name"
  if [[ ! -d "$source/.git" ]]; then
    git init -q "$source"
    git -C "$source" remote add origin "$url"
  fi
  git -C "$source" fetch --depth 1 origin "$revision"
  git -C "$source" checkout --detach FETCH_HEAD
  test "$(git -C "$source" rev-parse HEAD)" = "$revision"
  cmake -S "$source" -B "$source/build" -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_INSTALL_LIBDIR=lib64 -DCMAKE_BUILD_TYPE=Release "$@"
  cmake --build "$source/build" -j2
  DESTDIR="$DEST" cmake --install "$source/build"
  # Keep exact source and notices in the image for license compliance.
  local archive="$DEST/usr/share/onyx-os/sources/$name"
  mkdir -p "$archive"
  git -C "$source" archive HEAD | gzip > "$archive/source.tar.gz"
  printf '%s\n%s\n' "$url" "$revision" > "$archive/UPSTREAM"
}
build_effect blur https://github.com/can1357/kde-blur 4f86e779512716366554d59dbad2beed277dba6a -DBETTERBLUR_X11=OFF
build_effect corners https://github.com/matinlotfali/KDE-Rounded-Corners 66d7ce91a4f26062bba91bc7274ba85b6211391f
