@echo off
chcp 65001 >nul
REM Запуск на Windows двойным щелчком или из cmd: scripts\run_windows.bat
cd /d "%~dp0.."
where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
if not exist .venv (
  echo Создаю виртуальное окружение .venv ...
  %PY% -m venv .venv || goto :err
)
call .venv\Scripts\activate.bat || goto :err
python -m pip install --upgrade pip >nul
pip install -r requirements-dev.txt || goto :err
echo.
echo Откройте в браузере: http://127.0.0.1:8000   (остановка: Ctrl+C)
uvicorn app.main:app --reload
goto :eof
:err
echo Ошибка. Проверьте, что установлен Python 3.11+ (python --version).
pause
