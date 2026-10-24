@echo off
chcp 65001 >nul
title Criar ALF_picklescan.exe

echo ============================================
echo  ALF_picklescan - criar executavel Windows
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Python nao encontrado.
    echo Instale Python 3.11 ou superior em https://www.python.org/downloads/
    echo Durante a instalacao, marque "Add python.exe to PATH".
    pause
    exit /b 1
)

echo [1/3] A instalar dependencias...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo Falha na instalacao das dependencias.
    pause
    exit /b 1
)

echo.
echo [2/3] A gerar o executavel (pode demorar um minuto)...
python -m PyInstaller --onefile --windowed --name ALF_picklescan --clean --collect-all picklescan ALF_picklescan_gui.py
if errorlevel 1 (
    echo Falha na geracao do executavel.
    pause
    exit /b 1
)

echo.
echo [3/3] Limpeza...
if exist build rmdir /s /q build
if exist ALF_picklescan.spec del /q ALF_picklescan.spec

echo.
echo ============================================
echo  Pronto: dist\ALF_picklescan.exe
echo ============================================
pause
