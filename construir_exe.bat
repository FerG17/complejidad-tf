@echo off
REM Genera un .exe (Windows) con PyInstaller. Ejecutar dentro de la carpeta campus3d.
pip install pyinstaller matplotlib numpy
pyinstaller --noconfirm --onefile --windowed --name CampusRutasAccesibles --add-data "plano.png;." app.py
echo Listo: dist\CampusRutasAccesibles.exe
