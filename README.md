# ONYX OS 0.1 Alpha

ONYX OS is an experimental **Fedora 45 KDE Plasma desktop remix**. The goal is a real bootable, installable Linux Live ISO—not a website or a TV app.

## Status
The build workflow and basic ONYX desktop branding are provided. **The ISO has not yet been built or boot-tested.** Do not treat this repository as a finished operating system.

## Build with GitHub Actions
1. Open **Actions** → **Build ONYX OS Live ISO** → **Run workflow**.
2. Follow the **Build Fedora KDE image** job logs.
3. If the build and upload succeed, download the **ONYX-OS-Alpha-ISO** build artifact.
4. Extract the ZIP; verify the checksum; boot-test the ISO in a virtual machine before installing anything.
5. Use Rufus for a Live USB; choose **Try**, not Install, initially.

The build uses Fedora's official KIWI descriptions (branch `f45`, profile `KDE-Desktop-Live`), adds the ONYX crystal logo and desktop defaults **inside the ISO filesystem**, and generates a new Live ISO.

### Important limitations
- GitHub-hosted runners have limited free disk space; the Fedora KDE build may run out of space.
- The repository is **private**. GitHub Actions execution and large artifacts use your account's quotas; a multi-GB Fedora image can exceed the GitHub Free 500 MB shared artifact-storage allowance. Check billing settings. The workflow may fail at upload even if the ISO built.
- Fedora boot, installer and system package names may still display Fedora branding in this first alpha.
- The approved black-and-white flower photo is not in this initial GitHub upload; the first build uses the custom graphite ONYX wallpaper. We can add the original photo later.
- This is for x86_64 PCs, not the Hisense Roku TV.

## Local build
On a Fedora 45 x86_64 machine with sudo/root, internet, and substantial free disk:
```bash
bash build-onyx-iso.sh --check
sudo bash build-onyx-iso.sh
```
Expected target: `output/ONYX-OS-0.1-Alpha-x86_64.iso`.

Sources: [Fedora's build instructions](https://fedoraproject.org/wiki/Building_a_Fedora) and [KIWI descriptions](https://forge.fedoraproject.org/releng/kiwi-descriptions).
