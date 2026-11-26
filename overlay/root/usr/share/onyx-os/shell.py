#!/usr/bin/python3
"""ONYX Home and Settings for a native Plasma session."""
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
    ("Appearance", "Colors and desktop themes", "palette", "kcm_colors"),
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
    def __init__(self, page):
        super().__init__(application_id="org.onyx.Desktop." + page.capitalize())
        self.page = page
        self.window = None

    def do_activate(self):
        if self.window:
            self.window.present()
            return
        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title("ONYX Settings" if self.page == "settings" else "ONYX Home")
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.window.set_visual(visual)
        css = Gtk.CssProvider()
        css.load_from_path(str(ROOT / "shell.css"))
        Gtk.StyleContext.add_provider_for_screen(screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.window.set_default_size(890, 560)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_decorated(False)
        self.window.connect("key-press-event", self.key_press)
        self.window.connect("destroy", lambda *_: setattr(self, "window", None))
        frame = styled(Gtk.Box(), "frame")
        self.window.add(frame)
        rail = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8), "rail")
        frame.pack_start(rail, False, False, 0)
        brand = icon("crystal", 39)
        rail.pack_start(brand, False, False, 18)
        self.nav = {}
        for key, title, glyph in (("home", "Home", "house"),
                                  ("apps", "Applications", "layout-grid"),
                                  ("settings", "Settings", "settings-2")):
            item = button(icon(glyph, 23), lambda k=key: self.show_page(k), "nav")
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
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(170)
        body.pack_start(self.stack, True, True, 0)
        self.status = label("", "error")
        body.pack_end(self.status, False, False, 0)
        self.built_pages = set()
        for key, title in (("home", "Home"), ("apps", "Applications"), ("settings", "Settings")):
            panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
            panel.pack_start(label("ONYX OS", "wordmark"), False, False, 0)
            panel.pack_start(label(title, "heading"), False, False, 0)
            self.stack.add_named(panel, key)
        self.window.show_all()
        self.show_page(self.page)
        self.window.present()

    def key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            if self.stack.get_visible_child_name() == "detail":
                self.show_page("settings")
                return True
            widget.close()
            return True
        if event.state & Gdk.ModifierType.CONTROL_MASK and event.keyval == Gdk.KEY_f:
            self.show_page("apps")
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
        self.window.set_title("ONYX " + {"home":"Home", "apps":"Applications", "settings":"Settings"}[key])
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
        panel.pack_start(label("Quick launch", "section"), False, False, 0)
        cards = Gtk.Grid(column_spacing=12, row_spacing=12, column_homogeneous=True)
        for i, (name, desktop, glyph, color) in enumerate(FAVORITES):
            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
            art = icon(glyph, 38)
            art.set_halign(Gtk.Align.START)
            content.add(art)
            content.add(label(name, "card-title"))
            tile = button(content, lambda d=desktop: self.favorite(d), "card")
            styled(tile, color)
            cards.attach(tile, i % 2, i // 2, 1, 1)
        panel.pack_start(scroll(cards), True, True, 0)

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

    def setting_detail(self, title, module):
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
        more = button(label("More " + title.lower() + " settings  ›", "row-title"),
                      lambda: self.open_setting(module), "setting")
        body.add(more)
        self.stack.add_named(body, "detail")
        body.show_all()
        self.stack.set_visible_child_name("detail")

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
            self.report("Could not apply this setting. Open its full settings below.")
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
    page = "settings" if sys.argv[1:] == ["settings"] else "home"
    sys.exit(Shell(page).run(sys.argv[:1]))
