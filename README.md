# ONYX OS 0.1 Alpha

ONYX OS is an experimental **Fedora 45 KDE Plasma desktop remix**. The goal is a real bootable, installable Linux Live ISO—not a website or a TV app.

## Status
The build workflow and basic ONYX desktop branding are provided. **The ISO has not yet been built or boot-tested.** Do not treat this repository as a finished operating system.

## Build with GitHub Actions
1. Open **Actions** → **Build ONYX OS Live ISO** → **Run workflow**.
2. Follow the **Build Fedora KDE image** job logs.
3. If the build succeeds, open the repository's **Releases** and select **ONYX OS 0.1 Alpha**. The resulting image is **not** available under Actions artifacts.
4. If the ISO is smaller than GitHub's 2 GiB release-asset limit, download the single ISO and the SHA256 checksum. Otherwise download **every** numbered `.iso.partXX` file, the `.sha256` checksum and `COMBINE-ONYX-WINDOWS.cmd` into the same folder on a Windows computer; double-click the CMD to reconstruct the ISO and check its checksum.
5. Boot-test the reconstructed ISO in a virtual machine or Live USB before installing anywhere.
6. Use Rufus to write the ISO on a USB; choose **Try**, not Install, initially.

The build uses Fedora's official KIWI descriptions (branch `f45`, profile `KDE-Desktop-Live`), adds the ONYX crystal logo and desktop defaults **inside the ISO filesystem**, and generates a new Live ISO.

### Important limitations
- GitHub-hosted runners have limited free disk space; the Fedora KDE build may run out of space.
- The repository is **private**. GitHub Actions execution uses your account's included minutes or compute allowance. The workflow uses **GitHub Releases** (split assets where needed) rather than the 500 MB GitHub Actions artifact-storage allowance. Build/upload can still fail; check billing settings and logs.
- Fedora boot, installer and system package names may still display Fedora branding in this first alpha.
- The approved black-and-white flower photo is not in this initial GitHub upload; the first build uses the custom graphite ONYX wallpaper. We can add the original photo later.
- This is for x86_64 PCs, not the Hisense Roku TV.

## Understanding the first build
The first workflow completed the Fedora KIWI image compose but our wrapper searched the wrong folder and exited with `Expected exactly one ISO; found 0`. That wrapper has now been fixed to find the Fedora output under `output-build/`. A fresh workflow run is required to actually download and verify the ISO. The previous runner's ISO was discarded when the job ended.

**Windows storage:** Rebuilding split release assets needs enough free storage for both the parts and combined ISO. A Windows PC with less than 1 GB free cannot download and reassemble them locally. Use more space or another computer.

## Local build
On a Fedora 45 x86_64 machine with sudo/root, internet, and substantial free disk:
```bash
bash build-onyx-iso.sh --check
sudo bash build-onyx-iso.sh
```
Expected target: `output/ONYX-OS-0.1-Alpha-x86_64.iso`.

Sources: [Fedora's build instructions](https://fedoraproject.org/wiki/Building_a_Fedora) and [KIWI descriptions](https://forge.fedoraproject.org/releng/kiwi-descriptions).
