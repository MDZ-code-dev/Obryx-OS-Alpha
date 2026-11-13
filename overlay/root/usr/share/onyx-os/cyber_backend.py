"""Fixed Cyber Mode actions and an optional rootless Kali workspace."""
import argparse
import fcntl
import os
from pathlib import Path
import shutil
import subprocess
import sys

IMAGE = 'docker.io/kalilinux/kali-rolling:latest'
CONTAINER = 'onyx-kali'
PACKS = {
    'essentials': ('Kali essentials', 'kali-linux-headless'),
    'web': ('Web testing', 'kali-tools-web'),
    'forensics': ('Digital forensics', 'kali-tools-forensics'),
    'reverse': ('Reverse engineering', 'kali-tools-reverse-engineering'),
    'everything': ('Full Kali collection', 'kali-linux-everything'),
}
TOOLS = {
    'terminal': ('Cyber terminal', 'Open your ONYX command line', ['bash', '--noprofile', '--norc']),
    'interfaces': ('Network interfaces', 'Inspect local addresses and adapters', ['ip', '-brief', 'address']),
    'connections': ('Connections', 'Inspect current TCP and UDP connections', ['ss', '-tun']),
    'nmap': ('Nmap', 'Network discovery and service inspection • command help', ['nmap', '--help']),
    'wireshark': ('Wireshark', 'Open and analyze packet captures', ['wireshark']),
    'dns': ('DNS tools', 'Look up DNS records • command help', ['dig', '-h']),
    'logs': ('System logs', 'Review warnings from this boot', ['journalctl', '-b', '-p', 'warning', '--no-pager']),
    'openssl': ('OpenSSL', 'Certificate and cryptography tools • version details', ['openssl', 'version', '-a']),
}

def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

def is_live():
    try:
        return 'rd.live.image' in Path('/proc/cmdline').read_text()
    except OSError:
        return False

def prepare_kali():
    if is_live():
        raise RuntimeError('Kali downloads require a persistent installation. This live USB session loses changes at shutdown. The built-in tools work here.')
    if not shutil.which('podman'):
        raise RuntimeError('Podman is missing. Install it through the system software manager.')
    run(['podman', 'info'], stdout=subprocess.DEVNULL)
    exists = subprocess.run(['podman', 'container', 'exists', CONTAINER]).returncode
    if exists == 0:
        return
    if exists != 1:
        raise RuntimeError('Could not inspect the Kali workspace. Check the Podman error above.')
    if shutil.disk_usage(Path.home()).free < 5 * 1024**3:
        raise RuntimeError('At least 5 GB of free space is needed to create the Kali workspace.')
    run(['podman', 'pull', IMAGE])
    workspace = Path.home()/'.local/share/onyx-os/cyber/workspace'
    workspace.mkdir(parents=True, exist_ok=True)
    run(['podman', 'create', '--name', CONTAINER, '--label', 'org.onyx.cyber=1',
         '--volume', str(workspace)+':/workspace:Z', '--workdir', '/workspace',
         IMAGE, 'sleep', 'infinity'])

def kali(action):
    state = Path.home()/'.local/state/onyx-os'
    state.mkdir(parents=True, exist_ok=True)
    with (state/'cyber.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another Kali session or installation is already running. Close it first.')
        prepare_kali()
        run(['podman', 'start', CONTAINER], stdout=subprocess.DEVNULL)
        if action == 'kali-shell':
            print('Kali workspace • shared files: /workspace', flush=True)
            run(['podman', 'exec', '-it', CONTAINER, 'bash'])
            return
        key = action.removeprefix('install-')
        title, package = PACKS[key]
        required = 45 if key == 'everything' else 8
        if shutil.disk_usage(Path.home()).free < required * 1024**3:
            raise RuntimeError(f'Keep at least {required} GB free before installing {title}.')
        print(f'Installing {title}. APT will show the download and disk size before asking you to continue.', flush=True)
        run(['podman', 'exec', '-it', CONTAINER, 'apt-get', 'update'])
        # No automatic yes: APT shows its actual size and asks the user.
        run(['podman', 'exec', '-it', CONTAINER, 'apt-get', 'install', package])
        print('Installation completed. Open Kali terminal to use this collection.', flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=[*TOOLS, 'kali-shell', 'kali-stop', *['install-'+k for k in PACKS]])
    args = parser.parse_args()
    try:
        if args.action in TOOLS:
            command = TOOLS[args.action][2]
            if not shutil.which(command[0]):
                raise RuntimeError(command[0]+' is not installed.')
            if args.action == 'terminal':
                subprocess.run(['fastfetch'], check=False)
                os.environ['PS1'] = '\\[\\e[36m\\]ONYX CYBER\\[\\e[0m\\] \\w $ '
            run(command)
        elif args.action == 'kali-stop':
            run(['podman', 'stop', CONTAINER])
        else:
            kali(args.action)
        return 0
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print('\nCyber Mode: '+str(exc), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nCancelled. You can reopen Cyber Mode and retry.')
        return 130

if __name__ == '__main__':
    sys.exit(main())
