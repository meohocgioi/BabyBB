@echo off
title BabyBB - Bybit Multi-Sub Copy
set "DIR=%USERPROFILE%\BabyBB"
set "RAW=https://raw.githubusercontent.com/meohocgioi/BabyBB/main/bybit_copy.py"
if not exist "%DIR%" mkdir "%DIR%"
cd /d "%DIR%"

python --version >nul 2>&1
if errorlevel 1 (
  echo Chua co Python - dang thu cai tu dong...
  winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
  echo.
  echo Neu cai xong: DONG cua so nay va bam dup BabyBB.bat lan nua.
  echo Neu cai loi: tai Python tai https://www.python.org/downloads/ ^(tick "Add python.exe to PATH"^) roi chay lai.
  pause
  exit /b
)

if not exist bybit_copy.py (
  echo Dang tai tool lan dau...
  curl -L -s -o bybit_copy.py "%RAW%"
  if not exist bybit_copy.py (
    echo Khong tai duoc tool. Kiem tra mang roi chay lai.
    pause
    exit /b
  )
)

echo Dang kiem tra thu vien...
python -m pip install -q --disable-pip-version-check aiohttp
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
