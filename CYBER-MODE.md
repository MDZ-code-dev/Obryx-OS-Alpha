# Obryx Cyber Mode — 0.4 Alpha 4

Open Cyber Mode from Home or search for Obryx Cyber Mode.

## Included tools

The ISO includes Nmap, Wireshark, DNS utilities, OpenSSL, and Podman alongside
local network and system-log inspection. Commands open in a separate terminal.
Nmap opens its command help; no network scan runs on launch. Wireshark can open
saved capture files; live capture permissions remain managed by Fedora.

## Optional Kali workspace

On a persistent installation, Kali Workspace creates a rootless Podman container
from docker.io/kalilinux/kali-rolling. Fedora repositories are not changed.
Only ~/.local/share/onyx-os/cyber/workspace is mounted into the container as
/workspace. The host home directory, devices and host networking are not shared.
Use Stop Kali workspace to stop its background process.

Tool packs use the official metapackages kali-linux-headless, kali-tools-web,
kali-tools-forensics, kali-tools-reverse-engineering, and kali-linux-everything.
APT displays the actual size and asks before installing. The full collection
requires at least 45 GB free in this launcher; final size changes over time.

The live USB supports the included tools. Kali downloads are disabled there
because this build does not provide persistent storage. Installed systems need
working rootless Podman, including subordinate UID/GID mappings. Podman errors
remain visible in the terminal rather than silently changing system permissions.

The container supports command-line tools. Downloading GUI or hardware tools
does not guarantee they can run in it. The Learn tab links to official Kali
images for a full VM or dedicated machine, plus tool documentation and web labs.
Cyber Mode is a tool workspace, not an anonymity or automatic-hardening switch.

## Sources

- https://www.kali.org/docs/containers/official-kalilinux-docker-images/
- https://www.kali.org/docs/general-use/metapackages/
- https://docs.podman.io/en/latest/markdown/podman-run.1.html
- https://nmap.org/book/man.html
- https://www.wireshark.org/docs/
