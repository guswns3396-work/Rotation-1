@echo off
rem Double-click to start the IHS causal app. The first start sets up a private Python environment in the .venv folder
rem (a few minutes; needs the internet). Later starts take seconds. Close this window to stop the app.
setlocal EnableExtensions
title IHS causal app
cd /d "%~dp0"
set "VPY=%~dp0.venv\Scripts\python.exe"
set "PIPOPTS=--disable-pip-version-check"

if exist "%VPY%" (
  "%VPY%" -c "import numpy, pandas, pyarrow, yaml" >nul 2>nul && goto :installed
  echo The Python environment in .venv is incomplete or was moved; setting it up again.
  rmdir /s /q .venv
)

rem ---- find Python 3.9 or later: the py launcher, then python on the PATH (not the Microsoft Store placeholder)
set "BASE="
for %%V in (3.12 3.11 3.13 3.10 3.9 3.14) do (
  if not defined BASE (
    py -%%V -c "import sys, venv" >nul 2>nul && set "BASE=py -%%V"
  )
)
if not defined BASE (
  python -c "import sys, venv; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul && set "BASE=python"
)
if not defined BASE goto :uv

echo Setting up a private Python environment in .venv (first start only; a few minutes, needs the internet)...
%BASE% -m venv .venv || goto :fail
goto :deps

:uv
rem ---- no Python: use uv (it fetches its own Python), installing it first if the user agrees
set "UV="
for /f "delims=" %%U in ('where uv 2^>nul') do if not defined UV set "UV=%%U"
if not defined UV if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV=%USERPROFILE%\.local\bin\uv.exe"
if not defined UV if exist "%USERPROFILE%\.cargo\bin\uv.exe" set "UV=%USERPROFILE%\.cargo\bin\uv.exe"
if not defined UV (
  echo.
  echo Python 3.9 or later was not found on this computer.
  echo The app can set up its own Python with uv, a small installer from astral.sh. No administrator rights needed.
  choice /c YN /m "Install uv now"
  if errorlevel 2 goto :manual
  powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
  if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV=%USERPROFILE%\.local\bin\uv.exe"
  if not defined UV if exist "%USERPROFILE%\.cargo\bin\uv.exe" set "UV=%USERPROFILE%\.cargo\bin\uv.exe"
)
if not defined UV goto :manual
echo Setting up Python with uv (first start only; a few minutes, needs the internet)...
"%UV%" venv --seed --python 3.12 .venv || goto :fail

:deps
echo Installing numpy, pandas, pyarrow and pyyaml...
"%VPY%" -m pip install %PIPOPTS% -r requirements.txt || goto :fail
copy /y requirements.txt ".venv\installed-requirements.txt" >nul

:installed
fc /b requirements.txt ".venv\installed-requirements.txt" >nul 2>nul || (
  echo The requirements changed; updating .venv...
  "%VPY%" -m pip install %PIPOPTS% -r requirements.txt || goto :fail
  copy /y requirements.txt ".venv\installed-requirements.txt" >nul
)
rem the package itself is read from src\ in this folder, so updates to the code take effect at the next start
"%VPY%" -c "import sysconfig, pathlib; pathlib.Path(sysconfig.get_paths()['purelib'], 'ihs_causal_src.pth').write_text(str(pathlib.Path('src').resolve()) + '\n')" || goto :fail

echo Starting the app; it opens in your browser. Keep this window open while you use it.
"%VPY%" -m ihs_causal.cli serve %*
if errorlevel 1 pause
exit /b 0

:manual
echo.
echo Install Python from https://www.python.org/downloads/ (tick "Add python.exe to PATH"), then start this again.
start "" https://www.python.org/downloads/
pause
exit /b 1

:fail
echo.
echo Setup did not finish (see the messages above). Check the internet connection, delete the .venv folder, and start
echo this again. If it fails again, send the messages above to Drew.
pause
exit /b 1
