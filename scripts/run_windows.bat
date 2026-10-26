@echo off
chcp 65001 >nul
REM Запуск на Windows двойным щелчком или из cmd: scripts\run_windows.bat
cd /d "%~dp0.."

REM 1. Найти Python 3.11+
set "PY="
for %%V in (3.13 3.12 3.11) do (
  if not defined PY (
    py -%%V -c "import sys" >nul 2>nul && set "PY=py -%%V"
  )
)
if not defined PY (
  python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul && set "PY=python"
)
if not defined PY goto :nopython
echo Использую %PY%

REM 2. Пересоздать .venv, если он сделан на старом Python
if exist .venv (
  .venv\Scripts\python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul || (
    echo Окружение .venv создано на старом Python — пересоздаю ...
    rmdir /s /q .venv
  )
)
if not exist .venv (
  echo Создаю виртуальное окружение .venv ...
  %PY% -m venv .venv || goto :err
)
call .venv\Scripts\activate.bat || goto :err
python -m pip install --upgrade pip >nul
pip install -r requirements-dev.txt || goto :err
echo.
echo Откройте в браузере: http://127.0.0.1:8000   (остановка: Ctrl+C)
uvicorn app.main:app
goto :eof
:nopython
echo Нужен Python 3.11 или новее: https://www.python.org/downloads/windows/
pause
goto :eof
:err
echo Ошибка установки. Проверьте подключение к интернету и повторите.
pause
