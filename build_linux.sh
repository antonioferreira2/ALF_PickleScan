#!/usr/bin/env bash
# ALF_picklescan - criar executável Linux
#
# Requisitos (Ubuntu/Debian):
#   sudo apt install python3 python3-venv python3-tk
#
# Uso:
#   chmod +x build_linux.sh
#   ./build_linux.sh
#
# Resultado: dist/ALF_picklescan e dist/ALF_picklescan.sha256

set -euo pipefail
cd "$(dirname "$0")"

echo "=== ALF_picklescan: criar executável Linux ==="

if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "Erro: tkinter não está instalado. Instala com: sudo apt install python3-tk"
    exit 1
fi

echo "[1/4] Ambiente virtual..."
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo "[2/4] Dependências..."
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt pyinstaller --quiet

echo "[3/4] A gerar o executável..."
python -m PyInstaller --onefile --name ALF_picklescan --clean --collect-all picklescan ALF_picklescan_gui.py

echo "[4/4] SHA-256 e limpeza..."
(cd dist && sha256sum ALF_picklescan > ALF_picklescan.sha256)
rm -rf build ALF_picklescan.spec
deactivate

echo ""
echo "Pronto: dist/ALF_picklescan"
echo "Verificar: sha256sum -c dist/ALF_picklescan.sha256"
