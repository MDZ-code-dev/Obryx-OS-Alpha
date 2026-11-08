
# ONYX customizations execute after Fedora's config.sh operations.
echo "ONYX-OS: verifying embedded brand assets"
if [ ! -s /usr/share/onyx-os/onyx-logo.svg ] || [ ! -s /usr/share/wallpapers/ONYX/contents/images/1920x1080.png ]; then
  echo "FATAL: ONYX art is missing from the KIWI image root" >&2
  exit 37
fi
if [ ! -x /usr/local/bin/onyx-first-login ] || [ ! -f /etc/xdg/autostart/onyx-first-login.desktop ]; then
  echo "FATAL: ONYX login configuration missing" >&2
  exit 38
fi

# Fedora KDE's default wallpaper is selected through this symlink. Set the
# reference to ONYX in the image itself, not in a post-install theme kit.
if [ -L /usr/share/wallpapers/Default ]; then
  rm -f /usr/share/wallpapers/Default
elif [ -d /usr/share/wallpapers/Default ]; then
  mv /usr/share/wallpapers/Default /usr/share/wallpapers/Default.Fedora.backup
fi
ln -sfn /usr/share/wallpapers/ONYX /usr/share/wallpapers/Default

# Keep Fedora's internal distro ID so package managers and services continue
# to work, but expose ONYX to the desktop and About System dialog.
if [ -f /usr/lib/os-release ]; then
  sed -i \
    -e 's/^NAME=.*/NAME="ONYX OS"/' \
    -e 's/^PRETTY_NAME=.*/PRETTY_NAME="ONYX OS 0.2 Alpha (based on Fedora 45)"/' \
    /usr/lib/os-release
elif [ -f /etc/os-release ]; then
  sed -i \
    -e 's/^NAME=.*/NAME="ONYX OS"/' \
    -e 's/^PRETTY_NAME=.*/PRETTY_NAME="ONYX OS 0.2 Alpha (based on Fedora 45)"/' \
    /etc/os-release
fi
test -e /usr/share/wallpapers/Default/contents/images/1920x1080.png || {
  echo "FATAL: ONYX system wallpaper was not set" >&2; exit 39;
}
grep -q 'ONYX OS 0.2 Alpha' /usr/lib/os-release /etc/os-release 2>/dev/null || {
  echo "FATAL: ONYX OS branding not present in os-release" >&2; exit 40;
}
echo "ONYX-OS: default system wallpaper, dark UI configuration and OS name verified."
