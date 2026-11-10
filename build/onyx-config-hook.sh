
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
    -e 's/^PRETTY_NAME=.*/PRETTY_NAME="ONYX OS 0.3.1 Alpha"/' \
    /usr/lib/os-release
elif [ -f /etc/os-release ]; then
  sed -i \
    -e 's/^NAME=.*/NAME="ONYX OS"/' \
    -e 's/^PRETTY_NAME=.*/PRETTY_NAME="ONYX OS 0.3.1 Alpha"/' \
    /etc/os-release
fi
test -e /usr/share/wallpapers/Default/contents/images/1920x1080.png || {
  echo "FATAL: ONYX system wallpaper was not set" >&2; exit 39;
}
grep -q 'ONYX OS 0.3.1 Alpha' /usr/lib/os-release /etc/os-release 2>/dev/null || {
  echo "FATAL: ONYX OS branding not present in os-release" >&2; exit 40;
}
echo "ONYX-OS: default system wallpaper, dark UI configuration and OS name verified."

# ONYX 0.3 Plasma splash and desktop configuration.
if [ ! -s /usr/share/onyx-os/plasma-layout.js ] || [ ! -s /usr/share/plasma/look-and-feel/org.onyx.desktop/contents/splash/Splash.qml ]; then
  echo "FATAL: ONYX 0.3 desktop components are missing" >&2
  exit 41
fi
if [ ! -f /etc/xdg/autostart/onyx-desktop-setup.desktop ] || [ ! -f /usr/local/bin/onyx-desktop-setup ]; then
  echo "FATAL: ONYX 0.3 desktop initialization is missing" >&2
  exit 42
fi
chmod +x /usr/local/bin/onyx-desktop-setup
# Keep Breeze's complete Look-and-Feel package for stability.
# Select the ONYX splash independently; our custom package only supplies splash QML.
mkdir -p /etc/xdg
cat > /etc/xdg/ksplashrc <<'ONYX_SPLASH'
[KSplash]
Engine=KSplashQML
Theme=org.onyx.desktop
ONYX_SPLASH
echo "ONYX-OS: 0.3 splash and desktop assets embedded."
if [ ! -x /usr/bin/liveinst ] || [ ! -x /usr/local/bin/onyx-live-installer ] || [ ! -s /etc/xdg/autostart/onyx-live-installer.desktop ]; then
  echo "FATAL: interactive live installer or session launcher missing" >&2
  exit 43
fi

# Build the native color scheme from the packaged Breeze palette so every
# KDE color role is present, including disabled text and accessibility roles.
mkdir -p /usr/share/color-schemes
cp /usr/share/color-schemes/BreezeDark.colors /usr/share/color-schemes/OnyxGlass.colors
for group in Window Button View; do
  kwriteconfig6 --file /usr/share/color-schemes/OnyxGlass.colors --group "Colors:$group" --key BackgroundNormal "25,32,44"
  kwriteconfig6 --file /usr/share/color-schemes/OnyxGlass.colors --group "Colors:$group" --key DecorationFocus "158,207,226"
done
kwriteconfig6 --file /usr/share/color-schemes/OnyxGlass.colors --group General --key Name "ONYX Glass"
kwriteconfig6 --file /usr/share/color-schemes/OnyxGlass.colors --group "Colors:Selection" --key BackgroundNormal "59,97,119"

# Keep Plymouth's password and progress rendering. Supply the ONYX image
# directory before KIWI builds the live initramfs with dracut.
theme=/usr/share/plymouth/themes/onyx
cp -a /usr/share/plymouth/themes/spinner/. "$theme/"
rm -f "$theme/spinner.plymouth"
cp -f --remove-destination /usr/share/onyx-os/boot-logo.png "$theme/watermark.png"
plymouth-set-default-theme onyx
test "$(plymouth-set-default-theme)" = onyx || exit 44
test -s "$theme/watermark.png" || exit 45

mkdir -p /etc/dracut.conf.d
echo 'add_dracutmodules+=" plymouth "' > /etc/dracut.conf.d/51-onyx-splash.conf
test -x /usr/bin/gtk-launch && test -s /usr/share/plasma/plasmoids/org.onyx.home/contents/ui/main.qml || exit 46
# The upstream live welcome wizard advertises installation. ONYX opens its own
# launcher at first login. Use the installed plugin ID for the KDED preference.
for module in /usr/lib*/qt6/plugins/kf6/kded/*welcome*.so; do
  [ -f "$module" ] || continue
  plugin=$(basename "$module" .so)
  kwriteconfig6 --file /etc/xdg/kded6rc --group "Module-$plugin" --key autoload false
done
# KSplash resolves a LookAndFeel package before live-user autostart executes.
# Supply the base package's complete component set with ONYX overrides.
lf=/usr/share/plasma/look-and-feel
cp -an "$lf/org.kde.breeze.desktop/contents/." "$lf/org.onyx.desktop/contents/"
mkdir -p /etc/skel/.config /usr/share/icons/hicolor/scalable/apps
install -m 644 /usr/share/onyx-os/crystal.svg /usr/share/icons/hicolor/scalable/apps/onyx-crystal.svg
for dir in /etc/xdg /etc/skel/.config; do
  kwriteconfig6 --file "$dir/kdeglobals" --group KDE --key LookAndFeelPackage org.onyx.desktop
  kwriteconfig6 --file "$dir/ksplashrc" --group KSplash --key Theme org.onyx.desktop
  kwriteconfig6 --file "$dir/kded6rc" --group Module-plasma-welcome --key autoload false
done
for entry in /etc/xdg/autostart/*welcome*.desktop /usr/share/applications/org.kde.plasma-welcome.desktop; do
  [ -f "$entry" ] || continue
  mkdir -p /etc/skel/.config/autostart
  printf '[Desktop Entry]\nType=Application\nHidden=true\n' > "/etc/skel/.config/autostart/$(basename "$entry")"
done
sed -i '/^LOGO=/d; /^VARIANT=/d' /usr/lib/os-release
printf 'LOGO=onyx-crystal\nVARIANT="ONYX Desktop"\n' >> /usr/lib/os-release
