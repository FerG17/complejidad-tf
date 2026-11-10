@echo off
cd /d "%~dp0"
python --version >nul 2>&1 || (echo Instala Python 3.9+ desde python.org y marca "Add to PATH" & pause & exit /b)
python -m pip install -q -r requirements.txt
python app.py
pause
