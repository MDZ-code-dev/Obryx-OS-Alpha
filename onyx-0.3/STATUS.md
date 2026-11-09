# ONYX OS 0.3 Full Desktop — implementation status

## Implemented in the source branch
- Fedora 45 KDE live ISO recipe preserved, 0.3 build filename and separate GitHub prerelease tag.
- Automatic GitHub Actions build on push to `onyx-0.3-desktop`.
- KDE native floating centered panel layout and a one-time user-session initializer.
- ONYX QML Plasma splash assets with animated 3x3 loader.
- ONYX Store and ONYX Settings application launchers that open real Discover and KDE System Settings.
- Blur and dark desktop defaults (dependent on compositor/theme support).
- Fail-fast checks for desktop and splash assets in KIWI.

## Still to implement or verify
- Replace actual ISO GRUB menu labels with **Start ONYX OS** / **Install ONYX OS**, including installer boot handling.
- Verify Plasma layout API, panel positioning, session startup and splash loading on the resulting live image.
- Replace stock KDE launcher with a truly custom ONYX launcher UI.
- Custom ONYX Settings front-end, notifications, login and installer branding.
- App install/update tests and accessibility settings.
- Boot test on VM and ASUS laptop.

Do not treat a successful CI compose as proof that the UI works.

## Code review notes
- 2026-11-08: Audited build script, KIWI hook, GitHub workflow, session initializer and panel script against the committed source.
- Fixed a serious integration mistake: the ONYX splash-only look-and-feel package must **not** replace the complete Breeze Look-and-Feel package. Configure the splash independently through `/etc/xdg/ksplashrc`.
- Updated panel setup to create a replacement before removing the old panels, to reduce the chance of leaving the user without a taskbar.
- No ISO boot test has been performed. The boot-menu requirement remains open.
- The visual ONYX Store/Settings are currently named launchers for real KDE tools, **not** custom applications.
