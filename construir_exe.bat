@echo off
cd /d "%~dp0"
REM Genera dist\CampusRutasAccesibles.exe con PyInstaller (un solo archivo, sin consola).
python -m pip install -q -r requirements.txt pyinstaller || exit /b 1
python -m PyInstaller --noconfirm --onefile --windowed --name CampusRutasAccesibles --add-data "datos;datos" --collect-submodules OpenGL --collect-submodules pyqtgraph --exclude-module matplotlib app.py || exit /b 1
echo Listo: dist\CampusRutasAccesibles.exe
