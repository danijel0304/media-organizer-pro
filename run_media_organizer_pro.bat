@echo off
setlocal
cd /d "%~dp0media_organizer_pro"

python media_organizer_pro.py
if errorlevel 1 (
  echo.
  echo Media Organizer Pro could not start. Make sure Python 3 is installed and available as "python".
  echo If needed, install Python from https://www.python.org/downloads/windows/
  pause
)
