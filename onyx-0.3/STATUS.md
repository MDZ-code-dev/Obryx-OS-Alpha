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

## Handoff checkpoint — 2026-11-08 (America/Toronto)

- Found a critical build integration bug against the actual Fedora f45
  config.sh: it ends with `exit 0`, so the previously appended ONYX hook
  was unreachable. Added tools/prepare-kiwi.py to insert the hook before
  that terminal exit and fail if upstream structure changes.
- Explicitly include dbus-tools, Discover and Flatpak in the KIWI image.
- Panel now uses Plasma 6 center alignment, fit-content length and
  translucent opacity. Required widget creation is checked, failed partial
  panels are removed, other monitors' panels are preserved, and a panel
  version marker makes retries idempotent.
- Session initialization now requires ONYX_LAYOUT_OK in the D-Bus reply
  before writing its completion marker.
- Splash now uses the existing ONYX SVG and a real animated 3-by-3 grid.
  Uses the stage property expected by KSplashQML.
- Verified locally: source preflight, shell syntax, executable hook-order
  fixture, XML dependency injection, duplicate and changed-upstream rejection.
  Panel logic is still awaiting a real Plasma session test.
- GitHub run 42550203525 was building the earlier commit aa30a0e when
  inspected. It does not validate these new changes.
- Earlier failed run 42550189577 failed because validate-onyx-source.py was
  missing in that intermediate commit; the current branch contains it.
- No verified 0.3 ISO, VM boot, installer or hardware test in this session.
- Next: inspect the new Actions build, verify the final hook runs in its
  logs, test Plasma live, then implement custom Start/Settings/Welcome.
- Development paused at the user's request; no unattended development is
  promised. ONYX 0.2 and main were not changed.
