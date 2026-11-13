"""Render every Cyber tab and check launcher and live-session behavior."""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'overlay/root/usr/share/onyx-os'))
import cyber
app = cyber.Cyber()
app.register(None)
app.activate()
out = Path(sys.argv[1]); out.mkdir(exist_ok=True)
for page in ('tools', 'kali', 'learn'):
    app.tabs.set_visible_child_name(page)
    loop = cyber.GLib.MainLoop()
    cyber.GLib.timeout_add(400, loop.quit)
    loop.run()
    window = app.window.get_window()
    shot = cyber.Gdk.pixbuf_get_from_window(window, 0, 0, window.get_width(), window.get_height())
    assert shot
    shot.savev(str(out/('cyber-'+page+'.png')), 'png', [], [])
with patch.object(cyber.Gio.Subprocess, 'new') as launch:
    app.launch('interfaces')
    args = launch.call_args.args[0]
    assert args[0] == 'konsole' and args[-1] == 'interfaces'
    assert '--hold' in args
with patch.object(cyber, 'is_live', return_value=True), patch.object(app, 'launch') as launch:
    app.confirm('install-everything')
    launch.assert_not_called()
    assert 'persistent' in app.status.get_text()
app.window.destroy()
print('Cyber dashboard tabs, native launcher and live-session guard passed.')
