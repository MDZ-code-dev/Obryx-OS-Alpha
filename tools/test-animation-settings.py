"""Check mutually exclusive effect configuration without a running desktop."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

source = Path(__file__).resolve().parents[1] / 'overlay/root/usr/share/onyx-os/shell.py'
spec = importlib.util.spec_from_file_location('obryx_shell', source)
shell = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shell)


class AnimationSettings(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.messages = []
        self.subject = SimpleNamespace(
            apply_value=lambda args: self.calls.append(args) or True,
            report=self.messages.append,
            setting_detail=lambda *args: None)
        self.effects = (('magiclamp', 'Genie'), ('squash', 'Squash'))

    def test_each_choice_disables_competitors_and_reloads(self):
        for selected in ('magiclamp', 'squash', 'none'):
            self.calls.clear()
            self.assertTrue(shell.Shell.set_animation_effects(self.subject, self.effects, selected))
            values = {args[-2]: args[-1] for args in self.calls[:-1]}
            self.assertEqual(values, {effect + 'Enabled': str(effect == selected).lower()
                                      for effect, _ in self.effects})
            self.assertEqual(self.calls[-1][-1], 'org.kde.KWin.reconfigure')

    def test_invalid_selection_does_not_write(self):
        self.assertFalse(shell.Shell.set_animation_effects(self.subject, self.effects, 'unknown'))
        self.assertEqual(self.calls, [])

    def test_failed_write_does_not_claim_success_or_reload(self):
        self.subject.apply_value = lambda args: self.calls.append(args) or False
        self.assertFalse(shell.Shell.set_animation_effects(self.subject, self.effects, 'squash'))
        self.assertEqual(len(self.calls), 1)

    def test_failed_reload_explains_saved_state(self):
        self.subject.apply_value = lambda args: self.calls.append(args) or args[0] != 'dbus-send'
        self.assertFalse(shell.Shell.set_animation_effects(self.subject, self.effects, 'magiclamp'))
        self.assertIn('saved', self.messages[-1])

    def test_speed_notifies_desktop(self):
        self.assertTrue(shell.Shell.set_animation_speed(self.subject, '0.5'))
        self.assertIn('--notify', self.calls[0])
        self.assertEqual(self.calls[0][-2:], ['AnimationDurationFactor', '0.5'])


if __name__ == '__main__':
    unittest.main()
