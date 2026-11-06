@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set "ISO=ONYX-OS-0.1-Alpha-x86_64.iso"
if not exist "%ISO%.part00" (
  echo Could not find ONYX OS ISO parts in this folder.
  echo Download all .part00, .part01, etc. files from the same GitHub Release.
  pause
  exit /b 1
)
set "PIECES="
for /f "delims=" %%F in ('dir /b /on "%ISO%.part*"') do (
  if defined PIECES (
    set "PIECES=!PIECES!+%%F"
  ) else (
    set "PIECES=%%F"
  )
)
echo Reassembling %ISO% ...
copy /b !PIECES! "%ISO%"
if errorlevel 1 (
  echo ERROR: Could not combine the ISO parts.
  pause
  exit /b 1
)
echo.
echo Expected SHA256 checksum is recorded in %ISO%.sha256
certutil -hashfile "%ISO%" SHA256
echo.
echo Compare the computed SHA256 with the checksum file before using Rufus.
echo The ISO has not yet been boot-tested.
pause
