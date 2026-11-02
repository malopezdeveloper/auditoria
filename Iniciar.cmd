@echo off
cd /d "%~dp0"
py -3 -c "import tkinter" >nul 2>&1
if errorlevel 1 (
 echo Se requiere Python 3.12 o superior con Tcl/Tk. Instala Python y vuelve a ejecutar.
 pause
 exit /b 1
)
py -3 main.py
if errorlevel 1 pause
