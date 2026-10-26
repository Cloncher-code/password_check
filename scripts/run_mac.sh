#!/usr/bin/env bash
# Запуск на macOS / Linux:  bash scripts/run_mac.sh
set -euo pipefail
cd "$(dirname "$0")/.."

ok_version='import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'

# 1. Найти Python 3.11+ (системный python3 на macOS часто 3.9 — он не подходит)
PY=""
for c in python3.13 python3.12 python3.11 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "$ok_version" 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "Нужен Python 3.11 или новее. Установите: brew install python@3.12"
  echo "или скачайте установщик: https://www.python.org/downloads/macos/"
  exit 1
fi
echo "Использую $($PY --version) ($(command -v $PY))"

# 2. Пересоздать .venv, если он сделан на старом Python
if [ -d .venv ] && ! .venv/bin/python -c "$ok_version" 2>/dev/null; then
  echo "Окружение .venv создано на старом Python — пересоздаю ..."
  rm -rf .venv
fi
if [ ! -d .venv ]; then
  echo "Создаю виртуальное окружение .venv ..."
  "$PY" -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
pip install -r requirements-dev.txt
echo
echo "Откройте в браузере: http://127.0.0.1:8000   (остановка: Ctrl+C)"
# Без --reload: иначе uvicorn следит и за .venv и бесконечно перезапускается (BUG-04).
# Режим разработки с автоперезапуском — F5 в VS Code или инструкция 1.
uvicorn app.main:app
