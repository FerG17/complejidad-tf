@echo off
REM Genera un .exe (Windows) con PyInstaller (sin probar con la ventana pyqtgraph/OpenGL). Ejecutar en esta carpeta.
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --onefile --windowed --name CampusRutasAccesibles --add-data "plano.png;." --collect-submodules OpenGL --collect-submodules pyqtgraph --exclude-module matplotlib app.py
echo Listo: dist\CampusRutasAccesibles.exe
