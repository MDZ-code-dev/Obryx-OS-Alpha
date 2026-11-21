#!/usr/bin/python3
"""Obryx Home and Settings for a native Plasma session."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk

ROOT = Path(__file__).resolve().parent
FAVORITES = (
    ("Files", "org.kde.dolphin.desktop", "folder", "ice"),
    ("Browser", "org.mozilla.firefox.desktop", "compass", "violet"),
    ("Store", "onyx-store.desktop", "store", "mint"),
    ("Terminal", "org.kde.konsole.desktop", "terminal", "slate"),
)
SETTINGS = (
    ("Display", "Resolution, scale and multiple screens", "monitor", "kcm_kscreen"),
    ("Sound", "Speakers, microphones and volume", "volume-2", "kcm_pulseaudio"),
    ("Wi-Fi & network", "Connections and saved networks", "wifi", "kcm_networkmanagement"),
    ("Bluetooth", "Pair and manage devices", "bluetooth", "kcm_bluetooth"),
    ("Appearance", "Wallpaper and desktop animations", "palette", "kcm_colors"),
    ("Widgets", "Add clocks, calendars, media controls and more", "layout-grid", "obryx_widgets"),
    ("Keyboard", "Keyboard layouts and typing", "settings-2", "kcm_keyboard"),
    ("Shortcuts", "Global keyboard shortcuts", "settings-2", "kcm_keys"),
    ("Mouse", "Pointer speed and scrolling", "settings-2", "kcm_mouse"),
    ("Touchpad", "Tapping, scrolling and gestures", "settings-2", "kcm_touchpad"),
    ("Power & battery", "Sleep, brightness and energy use", "monitor", "kcm_powerdevilprofilesconfig"),
    ("Notifications", "App alerts, sounds and do not disturb", "volume-2", "kcm_notifications"),
    ("Fonts", "Font family, size and rendering", "palette", "kcm_fonts"),
    ("Window effects", "Animations and desktop effects", "layout-grid", "kcm_kwin_effects"),
    ("Window rules", "Window behaviour and opacity", "settings-2", "kcm_kwinrules"),
    ("All settings", "Open the full system settings", "settings-2", None),
)


def styled(widget, name):
    widget.get_style_context().add_class(name)
    return widget


def label(value, style):
    return styled(Gtk.Label(label=value, xalign=0), style)


def icon(name, size):
    image = GdkPixbuf.Pixbuf.new_from_file_at_scale(
        str(ROOT / "icons" / (name + ".png")), size, size, True)
    return Gtk.Image.new_from_pixbuf(image)


def button(child, callback, style):
    item = styled(Gtk.Button(), style)
    item.add(child)
    item.connect("clicked", lambda *_: callback())
    return item


def scroll(content):
    viewport = Gtk.ScrolledWindow()
    viewport.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    viewport.add(content)
    return viewport


class Shell(Gtk.Application):
    def __init__(self, page, query=""):
        super().__init__(application_id="org.onyx.Desktop." + page.capitalize())
        self.page = page
        self.initial_query = query
        self.window = None

    def do_activate(self):
        if self.window:
            if self.page == "home" and self.window.is_active():
                self.window.close()
                return
            self.window.present()
            return
        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title("Obryx " + {"settings": "Settings", "apps": "Search", "home": "Home"}[self.page])
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.window.set_visual(visual)
        css = Gtk.CssProvider()
        css.load_from_path(str(ROOT / "shell.css"))
        Gtk.StyleContext.add_provider_for_screen(screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        monitor = screen.get_monitor_workarea(screen.get_primary_monitor())
        self.window.set_default_size(min(680 if self.page == "home" else 960, monitor.width - 48), min(610 if self.page == "home" else 650, monitor.height - 100))
        self.window.set_resizable(True)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_decorated(False)
        self.window.set_app_paintable(True)
        self.window.connect("key-press-event", self.key_press)
        self.window.connect("destroy", lambda *_: setattr(self, "window", None))
        frame = styled(Gtk.Box(), "onyx-frame")
        self.window.add(frame)
        if self.page == "home":
            styled(frame, "start-frame")
        rail = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8), "rail")
        frame.pack_start(rail, False, False, 0)
        if self.page == "home":
            rail.set_no_show_all(True)
            rail.hide()
        brand = icon("crystal", 39)
        rail.pack_start(brand, False, False, 18)
        self.nav = {}
        for key, title, glyph in (("home", "Home", "house"),
                                  ("apps", "Search", "layout-grid"),
                                  ("settings", "Settings", "settings-2")):
            if key != self.page:
                continue
            item = button(icon(glyph, 23), lambda k=key: self.navigate(k), "nav")
            item.set_tooltip_text(title)
            item.get_accessible().set_name(title)
            self.nav[key] = item
            rail.pack_start(item, False, False, 0)
        close = button(icon("x", 19), self.window.close, "nav")
        close.set_tooltip_text("Close")
        rail.pack_end(close, False, False, 0)
        body = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12), "body")
        frame.pack_start(body, True, True, 0)
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(240)
        body.pack_start(self.stack, True, True, 0)
        self.status = label("", "error")
        body.pack_end(self.status, False, False, 0)
        self.built_pages = set()
        for key, title in (("home", "Home"), ("apps", "Applications"), ("settings", "Settings")):
            panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
            panel.pack_start(label("Obryx OS 0.4 · ALPHA 4", "wordmark"), False, False, 0)
            heading = Gtk.EventBox()
            heading.add(label(title, "heading"))
            heading.connect("button-press-event", self.move_window)
            if key != "home":
                panel.pack_start(heading, False, False, 0)
            self.stack.add_named(panel, key)
        self.window.show_all()
        self.show_page(self.page)
        if self.page == "apps" and self.initial_query:
            self.search.set_text(self.initial_query)
        self.window.present()

    def navigate(self, key):
        if key == self.page:
            self.show_page(key)
        else:
            Gio.Subprocess.new([sys.executable, str(ROOT / "shell.py"), key],
                               Gio.SubprocessFlags.NONE)
            if self.page == "home":
                self.window.close()

    def move_window(self, widget, event):
        if event.button == 1:
            self.window.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
            return True
        return False

    def key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            if self.stack.get_visible_child_name() == "detail":
                self.show_page("settings")
                return True
            widget.close()
            return True
        if event.state & Gdk.ModifierType.CONTROL_MASK and event.keyval == Gdk.KEY_f:
            self.navigate("apps")
            return True
        return False

    def show_page(self, key):
        if key not in self.built_pages:
            panel = self.stack.get_child_by_name(key)
            getattr(self, "build_" + key)(panel)
            panel.show_all()
            self.built_pages.add(key)
        self.stack.set_visible_child_name(key)
        self.status.hide()
        self.window.set_title("Obryx " + {"home":"Home", "apps":"Applications", "settings":"Settings"}[key])
        for name, item in self.nav.items():
            ctx = item.get_style_context()
            (ctx.add_class if name == key else ctx.remove_class)("selected")
        if key == "apps":
            self.search.grab_focus()

    def report(self, message):
        self.status.set_text(message)
        self.status.show()

    def launch(self, info):
        if info is None:
            self.report("This application is unavailable.")
            return
        try:
            info.launch([], self.window.get_display().get_app_launch_context())
            self.window.close()
        except GLib.Error as exc:
            self.report(exc.message)

    def favorite(self, desktop):
        try:
            info = Gio.DesktopAppInfo.new(desktop)
        except TypeError:
            info = None
        if info is None and desktop == "org.mozilla.firefox.desktop":
            info = Gio.AppInfo.get_default_for_uri_scheme("https")
        self.launch(info)

    def build_home(self, panel):
        search = Gtk.SearchEntry(placeholder_text="Search apps — press Enter")
        search.connect("activate", lambda entry: self.home_search(entry.get_text()))
        panel.pack_start(search, False, False, 0)
        heading = Gtk.Box(spacing=12)
        heading.pack_start(label("Pinned", "row-title"), True, True, 0)
        heading.pack_end(button(label("All apps  ›", "section"), lambda: self.navigate("apps"), "setting"), False, False, 0)
        panel.pack_start(heading, False, False, 0)
        grid = Gtk.Grid(column_spacing=8, row_spacing=8, column_homogeneous=True)
        pins = list(FAVORITES) + [
            ("Settings", "onyx-settings.desktop", "settings-2", ""),
            ("Cyber Mode", "onyx-cyber.desktop", "wifi", ""),
            ("Code", "org.kde.kate.desktop", "layout-grid", ""),
            ("Forge", "onyx-developer.desktop", "terminal", ""),
        ]
        for i, (name, desktop, glyph, _) in enumerate(pins):
            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            content.pack_start(icon(glyph, 32), False, False, 0)
            caption = label(name, "section")
            caption.set_xalign(0.5)
            content.pack_start(caption, False, False, 0)
            grid.attach(button(content, lambda d=desktop: self.favorite(d), "start-pin"), i % 4, i // 4, 1, 1)
        panel.pack_start(scroll(grid), True, True, 0)
        panel.pack_start(label("Projects", "row-title"), False, False, 0)
        panel.pack_start(button(label("Open your Projects folder", "section"), self.open_projects, "setting"), False, False, 0)
        footer = styled(Gtk.Box(spacing=12), "start-footer")
        footer.pack_start(label(GLib.get_real_name() or GLib.get_user_name(), "section"), True, True, 0)
        footer.pack_end(button(label("Power", "section"), self.power_menu, "setting"), False, False, 0)
        footer.pack_end(button(label("Lock", "section"), self.lock_screen, "setting"), False, False, 0)
        panel.pack_end(footer, False, False, 0)

    def home_search(self, query):
        Gio.Subprocess.new([sys.executable, str(ROOT / "shell.py"), "apps", "--query", query], Gio.SubprocessFlags.NONE)
        self.window.close()

    def open_projects(self):
        try:
            folder = Path.home() / "Projects"
            folder.mkdir(exist_ok=True)
            Gio.AppInfo.launch_default_for_uri(folder.as_uri(), None)
        except (OSError, GLib.Error) as exc:
            self.report(str(exc))

    def power_menu(self):
        self.apply_value(["dbus-send", "--session", "--print-reply", "--dest=org.kde.LogoutPrompt",
                          "/LogoutPrompt", "org.kde.LogoutPrompt.promptAll"])

    def lock_screen(self):
        self.apply_value(["dbus-send", "--session", "--print-reply", "--dest=org.freedesktop.ScreenSaver",
                          "/ScreenSaver", "org.freedesktop.ScreenSaver.Lock"])

    def build_apps(self, panel):
        self.search = Gtk.SearchEntry(placeholder_text="Search installed applications")
        panel.pack_start(self.search, False, False, 0)
        listing = Gtk.ListBox()
        listing.set_selection_mode(Gtk.SelectionMode.SINGLE)
        apps = sorted(Gio.AppInfo.get_all(), key=lambda a: (a.get_display_name() or '').casefold())
        for app in apps:
            name = app.get_display_name()
            if not name or not app.should_show() or app.get_id() in ("onyx-home.desktop", "org.kde.systemsettings.desktop", "liveinst.desktop") or (app.get_executable() or "").endswith("/liveinst"):
                continue
            row = Gtk.ListBoxRow()
            row.info = app
            row.search_text = (name + " " + (app.get_description() or "")).casefold()
            line = styled(Gtk.Box(spacing=15), "line")
            if app.get_icon():
                line.add(Gtk.Image.new_from_gicon(app.get_icon(), Gtk.IconSize.LARGE_TOOLBAR))
            line.add(label(name, "row-title"))
            row.add(line)
            listing.add(row)
        listing.set_filter_func(lambda row: self.search.get_text().casefold() in row.search_text)
        listing.connect("row-activated", lambda _, row: self.launch(row.info))
        self.search.connect("search-changed", lambda *_: listing.invalidate_filter())
        self.search.connect("activate", lambda *_: self.first_match(listing))
        panel.pack_start(scroll(listing), True, True, 0)

    def first_match(self, listing):
        listing.invalidate_filter()
        for row in listing.get_children():
            if row.get_child_visible():
                self.launch(row.info)
                return

    def build_settings(self, panel):
        rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for title, subtitle, glyph, module in SETTINGS:
            line = Gtk.Box(spacing=16)
            line.add(icon(glyph, 25))
            words = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            words.add(label(title, "row-title"))
            words.add(label(subtitle, "detail"))
            line.pack_start(words, True, True, 0)
            line.add(icon("chevron-right", 16))
            rows.add(button(line, lambda t=title, m=module: self.setting_detail(t, m), "setting"))
        panel.pack_start(scroll(rows), True, True, 0)

    def add_widgets(self):
        if self.apply_value(["dbus-send", "--session", "--print-reply",
                             "--dest=org.kde.plasmashell", "/PlasmaShell",
                             "org.kde.PlasmaShell.toggleWidgetExplorer"]):
            self.window.hide()

    def setting_detail(self, title, module):
        if module == "obryx_widgets":
            self.add_widgets()
            return
        if not module or module not in ("kcm_networkmanagement", "kcm_pulseaudio", "kcm_colors"):
            self.open_setting(module)
            return
        previous = self.stack.get_child_by_name("detail")
        if previous:
            self.stack.remove(previous)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        back = button(label("‹  Settings", "section"), lambda: self.show_page("settings"), "setting")
        back.set_halign(Gtk.Align.START)
        body.add(back)
        body.add(label(title, "heading"))
        if module == "kcm_pulseaudio":
            current = self.read_value(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"])
            if current.startswith("Volume:"):
                percent = round(float(current.split()[1]) * 100)
                slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, max(100, percent), 1)
                slider.set_digits(0)
                slider.set_value(percent)
                slider.connect("button-release-event", lambda control, _: self.set_volume(control))
                slider.connect("key-release-event", lambda control, _: self.set_volume(control))
                body.add(label("Output volume (%)", "row-title"))
                body.add(slider)
        elif module == "kcm_networkmanagement":
            state = self.read_value(["nmcli", "-t", "radio", "wifi"])
            if state in ("enabled", "disabled"):
                row = Gtk.Box(spacing=16)
                row.pack_start(label("Wi-Fi", "row-title"), True, True, 0)
                toggle = Gtk.Switch(active=state == "enabled")
                toggle.connect("state-set", lambda _, active: not self.apply_value(
                    ["nmcli", "radio", "wifi", "on" if active else "off"]))
                row.pack_end(toggle, False, False, 0)
                body.add(row)
        else:
            value = self.read_value(["kreadconfig6", "--file", "kdeglobals", "--group", "KDE",
                                     "--key", "AnimationDurationFactor", "--default", "1"])
            row = Gtk.Box(spacing=16)
            row.pack_start(label("Desktop animations", "row-title"), True, True, 0)
            toggle = Gtk.Switch(active=value not in ("0", "0.0"))
            toggle.connect("state-set", lambda _, active: not self.apply_value(
                ["kwriteconfig6", "--notify", "--file", "kdeglobals", "--group", "KDE",
                 "--key", "AnimationDurationFactor", "0.75" if active else "0"]))
            row.pack_end(toggle, False, False, 0)
            body.add(row)
        if module == "kcm_colors":
            body.add(button(label("Choose wallpaper…", "row-title"), self.choose_wallpaper, "setting"))
            body.add(label("Choose a JPG or PNG for every desktop screen.", "detail"))
            body.add(button(label("Add widgets…", "row-title"), self.add_widgets, "setting"))
            body.add(label("Drag widgets onto the desktop. Use Edit Mode to move or remove them.", "detail"))
            for caption, target in (("Colours & accent", "kcm_colors"),
                                    ("Icons", "kcm_icons"), ("Cursors", "kcm_cursortheme"),
                                    ("Window decorations", "kcm_kwindecoration")):
                body.add(button(label(caption + "  ›", "row-title"),
                                lambda m=target: self.open_setting(m), "setting"))
        more = button(label("Advanced KDE " + title.lower() + " settings  ›", "row-title"),
                      lambda: self.open_setting(module), "setting")
        if module != "kcm_colors":
            body.add(more)
        detail = scroll(body)
        self.stack.add_named(detail, "detail")
        detail.show_all()
        self.stack.set_visible_child_name("detail")

    def choose_wallpaper(self):
        chooser = Gtk.FileChooserDialog(title="Choose wallpaper", parent=self.window,
                                        action=Gtk.FileChooserAction.OPEN)
        chooser.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Apply", Gtk.ResponseType.OK)
        images = Gtk.FileFilter()
        images.set_name("Images (PNG, JPG)")
        images.add_mime_type("image/png")
        images.add_mime_type("image/jpeg")
        chooser.add_filter(images)
        if chooser.run() == Gtk.ResponseType.OK:
            path = Path(chooser.get_filename())
            self.apply_wallpaper(path)
        chooser.destroy()

    def apply_wallpaper(self, path):
        try:
            path = Path(path)
            GdkPixbuf.Pixbuf.new_from_file_at_scale(str(path), 320, 200, True)
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()[:20]
            target = Path.home() / ".local/share/onyx-os/wallpapers" / (digest + path.suffix.lower())
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            script = """var ds = desktops(); if (!ds.length) throw Error('No desktop');
                for (var i=0; i<ds.length; i++) {
                var d = ds[i]; d.wallpaperPlugin = 'org.kde.image';
                d.currentConfigGroup = ['Wallpaper', 'org.kde.image', 'General'];
                d.writeConfig('Image', %s); }""" % json.dumps(target.as_uri())
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            reply = bus.call_sync('org.kde.plasmashell', '/PlasmaShell',
                'org.kde.PlasmaShell', 'evaluateScript', GLib.Variant('(s)', (script,)),
                GLib.VariantType.new('(s)'), Gio.DBusCallFlags.NONE, 5000, None)
            result = reply.unpack()[0]
            if 'Error' in result or 'Exception' in result:
                raise ValueError(result)
            self.report("Wallpaper applied.")
            return True
        except (OSError, GLib.Error, ValueError) as exc:
            self.report("Could not apply wallpaper: " + str(exc))
            return False

    def read_value(self, args):
        try:
            return subprocess.run(args, text=True, capture_output=True, check=True,
                                  timeout=2).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""

    def apply_value(self, args):
        try:
            subprocess.run(args, capture_output=True, check=True, timeout=3)
            return True
        except (OSError, subprocess.SubprocessError):
            self.report("Could not apply this setting. Please try again.")
            return False

    def set_volume(self, control):
        self.apply_value(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@",
                          str(round(control.get_value())) + "%"])
        return False

    def open_setting(self, module):
        try:
            Gio.Subprocess.new(["systemsettings"] + ([module] if module else []),
                               Gio.SubprocessFlags.NONE)
        except GLib.Error as exc:
            self.report(exc.message)


if __name__ == "__main__":
    page = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ("home", "apps", "settings") else "home"
    query = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--query" else ""
    sys.exit(Shell(page, query).run(sys.argv[:1]))
