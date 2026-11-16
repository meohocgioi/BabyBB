@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Bybit Multi-Sub Copy
where python >nul 2>nul
if errorlevel 1 (
  echo Chua cai Python. Tai tai https://www.python.org/downloads/ ^(nho tick "Add python.exe to PATH"^) roi chay lai file nay.
  pause
  exit /b
)
echo Dang kiem tra thu vien...
python -m pip install -q --disable-pip-version-check aiohttp telethon
set BYBITCOPY_LAUNCHER=1
:loop
python bybit_copy.py
if %errorlevel%==42 (
  set BYBITCOPY_RESTARTED=1
  goto loop
)
echo.
echo Tool da dung. Bam phim bat ky de dong cua so.
pause >nul
