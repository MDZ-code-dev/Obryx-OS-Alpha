"""Render Developer and verify starter creation never overwrites a project."""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'overlay/root/usr/share/onyx-os'))
import developer

app = developer.Developer()
app.register(None)
app.activate()
loop = developer.GLib.MainLoop()
developer.GLib.timeout_add(400, loop.quit)
loop.run()
window = app.window.get_window()
shot = developer.Gdk.pixbuf_get_from_window(window, 0, 0, window.get_width(), window.get_height())
assert shot
out = Path(sys.argv[1]); out.mkdir(exist_ok=True)
shot.savev(str(out/'developer.png'), 'png', [], [])
with tempfile.TemporaryDirectory() as folder, patch.object(app, 'projects', return_value=Path(folder)), patch.object(app, 'open'):
    app.examples()
    source = Path(folder)/'OnyxExamples/python/main.py'
    assert source.exists()
    source.write_text('my existing code')
    app.examples()
    assert source.read_text() == 'my existing code'
app.window.destroy()
print('Developer renders; starter projects preserve existing user code.')
