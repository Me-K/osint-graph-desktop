@echo off
setlocal
cd /d "%~dp0"
if exist "dist\OSINTGraph\OSINTGraph.exe" (
    start "" "dist\OSINTGraph\OSINTGraph.exe"
    exit /b 0
)
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "main.py"
    exit /b 0
)
echo Lancez d'abord build.ps1 sur un poste de preparation, ou copiez le dossier portable OSINTGraph complet.
pause
exit /b 1
