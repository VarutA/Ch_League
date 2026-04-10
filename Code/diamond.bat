@echo off
REM Run from repo root:  Code\diamond.bat cal
set "SCRIPT_DIR=%~dp0"
set "REPO=%SCRIPT_DIR%.."
cd /d "%REPO%"
python "%SCRIPT_DIR%diamond.py" %*
