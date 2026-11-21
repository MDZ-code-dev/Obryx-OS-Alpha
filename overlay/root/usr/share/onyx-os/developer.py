"""Native development shortcuts and ESP32 setup resources."""
import shutil
import sys
from pathlib import Path
from gi.repository import Gio, GLib
from shell import Gtk, Gdk, styled, label, button, scroll, ROOT

class Developer(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='org.onyx.Desktop.Developer')
        self.window = None

    def do_activate(self):
        if self.window:
            self.window.present()
            return
        self.window = Gtk.ApplicationWindow(application=self, title='ONYX Developer')
        self.window.connect('destroy', lambda *_: setattr(self, 'window', None))
        self.window.set_default_size(700, 580)
        css = Gtk.CssProvider()
        css.load_from_path(str(ROOT/'shell.css'))
        Gtk.StyleContext.add_provider_for_screen(self.window.get_screen(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        body = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12), 'body')
        styled(body, 'onyx-frame')
        self.window.add(scroll(body))
        body.add(label('Developer', 'heading'))
        body.add(label('Code, build, debug and connect your boards.', 'section'))
        for title, action in [
            ('Code editor — Kate', lambda: self.command(['kate'])),
            ('Project terminal', self.terminal),
            ('Create starter projects — Python, C++ and ESP32 Arduino', self.examples),
            ('List connected serial boards', lambda: self.command(['konsole', '--separate', '--hold', '-e', '/usr/bin/python3', '-m', 'serial.tools.list_ports', '-v'])),
        ]:
            body.add(button(label(title, 'row-title'), action, 'setting'))
        body.add(label('Optional board tools — internet and disk space required', 'section'))
        for title, url in [
            ('Download Arduino IDE', 'https://www.arduino.cc/en/software'),
            ('ESP32 Arduino board setup', 'https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html'),
            ('Install ESP-IDF — official Espressif guide', 'https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/linux-setup.html'),
            ('PlatformIO setup guide', 'https://docs.platformio.org/en/latest/core/installation/index.html'),
        ]:
            body.add(button(label(title, 'row-title'), lambda u=url: self.open(u), 'setting'))
        note = label('Git, Python, C/C++, CMake, Ninja and GDB are included. Board toolchains are separate downloads. Save projects on persistent storage; live USB changes are lost at shutdown.', 'detail')
        note.set_line_wrap(True)
        body.add(note)
        self.status = label('', 'error')
        self.status.set_line_wrap(True)
        body.add(self.status)
        self.window.show_all()

    def command(self, args):
        try:
            Gio.Subprocess.new(args, Gio.SubprocessFlags.NONE)
        except GLib.Error as exc:
            self.status.set_text(exc.message)

    def open(self, uri):
        try:
            Gio.AppInfo.launch_default_for_uri(uri, None)
        except GLib.Error as exc:
            self.status.set_text(exc.message)

    def projects(self):
        folder = Path.home()/'Projects'
        folder.mkdir(exist_ok=True)
        return folder

    def terminal(self):
        try:
            self.command(['konsole', '--separate', '--workdir', str(self.projects())])
        except OSError as exc:
            self.status.set_text(str(exc))

    def examples(self):
        try:
            target = self.projects()/'OnyxExamples'
            if not target.exists():
                shutil.copytree(ROOT/'templates', target)
            self.open(target.as_uri())
        except OSError as exc:
            self.status.set_text(str(exc))

if __name__ == '__main__':
    sys.exit(Developer().run(sys.argv[:1]))
