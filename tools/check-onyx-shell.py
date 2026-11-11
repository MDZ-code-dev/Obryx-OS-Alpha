"""Exercise the native GTK pages on a display and capture the rendered windows."""
import importlib.util
import sys
from pathlib import Path

source = Path(__file__).resolve().parents[1] / "overlay/root/usr/share/onyx-os/shell.py"
spec = importlib.util.spec_from_file_location("onyx_shell", source)
shell = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shell)
app = shell.Shell("home")
app.register(None)
app.activate()
output = Path(sys.argv[1])
output.mkdir(parents=True, exist_ok=True)
for page in ("home", "apps", "settings"):
    app.show_page(page)
    loop = shell.GLib.MainLoop()
    shell.GLib.timeout_add(400, loop.quit)
    loop.run()
    assert app.stack.get_visible_child_name() == page
    if page == "apps":
        app.search.set_text("no-onyx-test-app-exists")
    window = app.window.get_window()
    capture = shell.Gdk.pixbuf_get_from_window(window, 0, 0, window.get_width(), window.get_height())
    assert capture is not None
    capture.savev(str(output / (page + ".png")), "png", [], [])
app.setting_detail("Appearance", "kcm_colors")
assert app.stack.get_visible_child_name() == "detail"
app.window.destroy()

# Every launcher owns an independent application ID and navigation rail.
assert list(app.nav) == ['home']
for page in ('apps', 'settings'):
    instance = shell.Shell(page)
    instance.register(None)
    instance.activate()
    assert list(instance.nav) == [page]
    assert instance.get_application_id().endswith(page.capitalize())
    instance.window.destroy()

# Exercise wallpaper decoding, durable copy and the exact Plasma D-Bus request.
import tempfile
from unittest.mock import patch
with tempfile.TemporaryDirectory() as folder:
    picture = Path(folder) / 'wallpaper with spaces.png'
    pixbuf = shell.GdkPixbuf.Pixbuf.new(shell.GdkPixbuf.Colorspace.RGB, False, 8, 32, 32)
    pixbuf.fill(0x335577ff)
    pixbuf.savev(str(picture), 'png', [], [])
    calls = []
    class Bus:
        def call_sync(self, *args):
            calls.append(args)
            return shell.GLib.Variant('(s)', ('',))
    messages = []
    with patch.object(shell.Path, 'home', return_value=Path(folder)), patch.object(shell.Gio, 'bus_get_sync', return_value=Bus()), patch.object(app, 'report', side_effect=messages.append):
        assert app.apply_wallpaper(picture)
        assert len(calls) == 1
        assert calls[0][0:4] == ('org.kde.plasmashell', '/PlasmaShell', 'org.kde.PlasmaShell', 'evaluateScript')
        assert 'desktops()' in calls[0][4].unpack()[0]
        assert len(list((Path(folder)/'.local/share/onyx-os/wallpapers').glob('*.png'))) == 1
        assert not app.apply_wallpaper(Path(folder)/'missing.png')
        assert len(calls) == 1
print('Separate application IDs and wallpaper apply/error tests passed.')
