@echo off
:: ============================================================
::  launch.bat — Launch Refat's Android Full Backup V1.0
::  Multi-Device  |  MTKClient Engine
:: ============================================================

title Refat's Android Full Backup V1.0 — Launcher

echo.
echo  Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install Python and add it to PATH.
    pause
    exit /b 1
)

echo  Checking dependencies...
python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo  Installing customtkinter...
    pip install customtkinter
)

python -c "from PIL import Image" >nul 2>&1
if errorlevel 1 (
    echo  Installing Pillow...
    pip install Pillow
)

echo  Launching GUI...
start "" pythonw gui.py
