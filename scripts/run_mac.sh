#!/usr/bin/env bash
# Запуск на macOS / Linux:  bash scripts/run_mac.sh
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -d .venv ]; then
  echo "Создаю виртуальное окружение .venv ..."
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
pip install -r requirements-dev.txt
echo
echo "Откройте в браузере: http://127.0.0.1:8000   (остановка: Ctrl+C)"
uvicorn app.main:app --reload
