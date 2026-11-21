#!/usr/bin/python3
"""Obryx Cyber Mode: native tools, learning resources and optional Kali packs."""
import sys
import shutil
from pathlib import Path
from gi.repository import Gio, GLib
from shell import Gtk, Gdk, styled, label, button, scroll, ROOT
from cyber_backend import TOOLS, PACKS, is_live

class Cyber(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='org.onyx.Desktop.Cyber')
        self.window = None

    def do_activate(self):
        if self.window:
            self.window.present()
            return
        self.window = Gtk.ApplicationWindow(application=self, title='Obryx Cyber Mode')
        self.window.connect('destroy', lambda *_: setattr(self, 'window', None))
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.window.set_visual(visual)
        css = Gtk.CssProvider()
        css.load_from_path(str(ROOT/'shell.css'))
        Gtk.StyleContext.add_provider_for_screen(screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        area = screen.get_monitor_workarea(screen.get_primary_monitor())
        self.window.set_default_size(min(1000, area.width-48), min(700, area.height-100))
        self.window.set_position(Gtk.WindowPosition.CENTER)
        frame = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16), 'onyx-frame')
        styled(frame, 'cyber-body')
        self.window.add(frame)
        frame.add(label('Obryx OS 0.4 · ALPHA 4', 'wordmark'))
        frame.add(label('Cyber Mode', 'heading'))
        frame.add(label('Explore networks. Inspect systems. Build your skills.', 'section'))
        self.tabs = Gtk.Stack()
        self.tabs.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.tabs.set_transition_duration(240)
        switch = Gtk.StackSwitcher(stack=self.tabs)
        frame.add(switch)
        frame.pack_start(self.tabs, True, True, 0)
        self.status = label('', 'error')
        self.status.set_line_wrap(True)
        frame.pack_end(self.status, False, False, 0)
        self.add_tools()
        self.add_kali()
        self.add_learning()
        self.window.show_all()

    def page(self, key, title):
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.tabs.add_titled(scroll(body), key, title)
        return body

    def row(self, title, detail, callback):
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        body.add(label(title, 'row-title'))
        description = label(detail, 'detail')
        description.set_line_wrap(True)
        body.add(description)
        return button(body, callback, 'setting')

    def add_tools(self):
        body = self.page('tools', 'Tools')
        grid = Gtk.Grid(column_spacing=10, row_spacing=10, column_homogeneous=True)
        for i, (key, (title, description, command)) in enumerate(TOOLS.items()):
            available = shutil.which(command[0]) is not None
            row = self.row(title, description if available else 'Not installed on this system', lambda k=key: self.launch(k))
            row.set_sensitive(available)
            grid.attach(row, i % 2, i // 2, 1, 1)
        body.add(grid)
        body.add(label('Tools launch on demand. Network inspection does not start automatically.', 'detail'))

    def add_kali(self):
        body = self.page('kali', 'Kali workspace')
        note = label('Optional download • separate from Fedora • internet required', 'section')
        note.set_line_wrap(True)
        body.add(note)
        if is_live():
            note = label('Live USB: use the built-in tools here. Kali downloads need a persistent installation so tools and files survive a restart.', 'detail')
            note.set_line_wrap(True)
            body.add(note)
        body.add(self.row('Kali terminal', 'Create or reopen your Kali command-line workspace', lambda: self.confirm('kali-shell')))
        for key, (title, package) in PACKS.items():
            detail = 'Optional tool pack • APT shows the actual size before installing'
            if key == 'everything':
                detail = 'Large download • keep at least 45 GB free • not all tools work in a container'
            body.add(self.row(title, detail, lambda k=key: self.confirm('install-'+k)))
        body.add(self.row('Stop Kali workspace', 'Stop its background container when you finish', lambda: self.launch('kali-stop')))
        note = label('This workspace supports terminal tools. GUI tools, USB access, Wi-Fi monitor mode and GPU access may need a full Kali VM or dedicated hardware.', 'detail')
        note.set_line_wrap(True)
        body.add(note)

    def add_learning(self):
        body = self.page('learn', 'Learn')
        for title, detail, url in [
            ('Kali tool catalog', 'Official tool descriptions and documentation', 'https://www.kali.org/tools/'),
            ('Wireshark guide', 'Learn to inspect packet captures', 'https://www.wireshark.org/docs/wsug_html_chunked/'),
            ('Nmap guide', 'Learn network discovery and scan options', 'https://nmap.org/book/man.html'),
            ('Web Security Academy', 'Guided web-security lessons and practice labs', 'https://portswigger.net/web-security'),
            ('Full Kali images', 'Official images for a separate VM or machine', 'https://www.kali.org/get-kali/')]:
            body.add(self.row(title, detail, lambda u=url: self.open_url(u)))

    def confirm(self, action):
        if is_live():
            self.status.set_text('Kali downloads require a persistent installation. The Tools tab works in this live session.')
            return
        dialog = Gtk.MessageDialog(transient_for=self.window, modal=True, message_type=Gtk.MessageType.QUESTION,
                                   buttons=Gtk.ButtonsType.OK_CANCEL, text='Open the Kali workspace?')
        dialog.format_secondary_text('The first use downloads the official Kali container. Tool installation runs in a terminal and shows its actual size before asking you to continue. Files are shared only through the Cyber workspace folder.')
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            self.launch(action)

    def launch(self, action):
        try:
            if action == 'wireshark':
                args = ['wireshark']
            else:
                args = ['konsole', '--separate', '--hold', '-e', sys.executable, str(ROOT/'cyber_backend.py'), action]
            Gio.Subprocess.new(args, Gio.SubprocessFlags.NONE)
            self.status.set_text('Opened in a separate window.')
        except GLib.Error as exc:
            self.status.set_text(exc.message)

    def open_url(self, url):
        try:
            Gio.AppInfo.launch_default_for_uri(url, None)
        except GLib.Error as exc:
            self.status.set_text(exc.message)

if __name__ == '__main__':
    sys.exit(Cyber().run(sys.argv))
