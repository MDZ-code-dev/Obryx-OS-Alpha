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
