@echo off
setlocal
cd /d "%~dp0"
set "ISO=ONYX-OS-0.4-Alpha2-x86_64.iso"
if not exist "%ISO%.sha256" goto missing
if not exist "%ISO%.part00" goto missing
if exist "%ISO%" goto verify
copy /b "%ISO%.part*" "%ISO%.assembling" >nul
if errorlevel 1 goto failed
powershell -NoProfile -Command "$expected=((Get-Content -LiteralPath ($env:ISO+'.sha256') -Raw).Trim() -split '\s+')[0]; if ((Get-FileHash -LiteralPath ($env:ISO+'.assembling')).Hash -ne $expected) {exit 1}"
if errorlevel 1 goto failed
move /y "%ISO%.assembling" "%ISO%" >nul
if errorlevel 1 goto failed
:verify
powershell -NoProfile -Command "$expected=((Get-Content -LiteralPath ($env:ISO+'.sha256') -Raw).Trim() -split '\s+')[0]; if ((Get-FileHash -LiteralPath $env:ISO).Hash -ne $expected) {exit 1}"
if errorlevel 1 goto failed
echo ISO verified. Select %ISO% in Rufus.
pause
exit /b 0
:missing
echo Download all numbered parts and the SHA256 file into this folder.
pause
exit /b 1
:failed
if exist "%ISO%.assembling" del "%ISO%.assembling"
echo Assembly or checksum failed. Check free space and download every numbered part. If a previous ISO exists, move it aside before retrying.
pause
exit /b 1
