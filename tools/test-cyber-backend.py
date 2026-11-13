"""Check fixed commands, live-session guard and optional-pack command routing."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('cyber_backend', Path(__file__).resolve().parents[1]/'overlay/root/usr/share/onyx-os/cyber_backend.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

class CyberTests(unittest.TestCase):
    def test_live_blocks_download_before_podman(self):
        with patch.object(b, 'is_live', return_value=True), patch.object(b, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'persistent'):
                b.prepare_kali()
            run.assert_not_called()

    def test_container_has_only_workspace_mount(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(b.Path, 'home', return_value=Path(folder)), patch.object(b, 'is_live', return_value=False), patch.object(b.shutil, 'which', return_value='/usr/bin/podman'), patch.object(b.shutil, 'disk_usage', return_value=type('Disk', (), {'free':60*1024**3})()), patch.object(b, 'run') as run, patch.object(b.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)):
            b.prepare_kali()
            calls = [c.args[0] for c in run.call_args_list]
            create = calls[-1]
            self.assertIn(b.IMAGE, create)
            self.assertNotIn('--privileged', create)
            self.assertNotIn('--network=host', create)
            self.assertEqual(create.count('--volume'), 1)
            self.assertTrue(create[create.index('--volume')+1].endswith(':/workspace:Z'))

    def test_pack_selection_and_confirmation(self):
        for key, (_, package) in b.PACKS.items():
            with tempfile.TemporaryDirectory() as folder, patch.object(b.Path, 'home', return_value=Path(folder)), patch.object(b, 'prepare_kali'), patch.object(b.shutil, 'disk_usage', return_value=type('Disk', (), {'free':60*1024**3})()), patch.object(b, 'run') as run:
                b.kali('install-'+key)
                install = run.call_args_list[-1].args[0]
                self.assertEqual(install[-3:], ['apt-get', 'install', package])
                self.assertNotIn('-y', install)

    def test_no_automatic_scan(self):
        self.assertEqual(b.TOOLS['nmap'][2], ['nmap', '--help'])
        self.assertEqual(b.TOOLS['interfaces'][2], ['ip', '-brief', 'address'])

if __name__ == '__main__':
    unittest.main()
