@echo off
REM Run from repo root:  Code\gold.bat group-create -y
set "SCRIPT_DIR=%~dp0"
set "REPO=%SCRIPT_DIR%.."
cd /d "%REPO%"
python "%SCRIPT_DIR%gold.py" %*
