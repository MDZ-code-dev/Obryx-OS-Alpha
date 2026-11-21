# ONYX motion update

The supplied Windhawk Taskbar Dock Animation by Ph0en1x-dev is the reference for continuous pointer-distance cosine magnification. ONYX implements this in its existing Qt Quick dock; it does not load Windows hooks. The MacOS Minimize Animation by Abdullah Masood is the visual reference for the native KWin Magic Lamp effect. The Taskbar and Start Menu Styler references by m417z guide the existing rounded glass panels. No Windhawk source is bundled or copied into this update.

- Dock: fractional pointer position, continuous cosine falloff, subpixel lift, cubic easing and a subtle press response. Animation timings follow Kirigami, including the desktop animation preference.
- Windows: KWin scale/fade at 94% on opening and 97% on closing, 260 ms before the global speed factor; Magic Lamp at 420 ms before the global speed factor.
- Settings: directional page transitions. Cards and search fields: soft hover/focus transitions without layout movement.

References: https://github.com/Ph0en1x-dev ; https://github.com/Abdullah-Masood-05 ; https://github.com/m417z/my-windhawk-mods ; https://invent.kde.org/plasma/kwin .

The supplied TikTok link could not be viewed. No claim is made that this matches that video. Validate animations on the actual KDE live desktop before publishing an ISO.
