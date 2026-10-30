# Инструкция 1. Запуск локально на Windows и macOS

Для кого: любой участник команды, в том числе без опыта Python. Время: 10–15 минут.

Результат: в браузере открыта страница http://127.0.0.1:8000, тесты зелёные.

## 0. Что понадобится

| Что | Версия | Зачем |
|---|---|---|
| Python | 3.11, 3.12 или 3.13 | запуск приложения |
| Папка проекта | архив `password-checker.zip` или клон из GitHub | код |
| Браузер | Chrome, Firefox или Edge последней версии | интерфейс |

Интернет нужен только для установки библиотек (шаг 3). Само приложение работает без интернета.

---

## Windows 10 / 11

### Шаг 1. Установить Python

1. Откройте https://www.python.org/downloads/windows/ и скачайте установщик Python 3.12 (Windows installer, 64-bit).
2. В первом окне установщика **поставьте галочку «Add python.exe to PATH»**, затем нажмите «Install Now».
3. Проверьте: откройте «Командную строку» (Win+R → `cmd` → Enter) и выполните:

```bat
py --version
```

Должно появиться `Python 3.12.x`. Если команда `py` не найдена, попробуйте `python --version`.

Вариант для опытных: `winget install Python.Python.3.12`.

### Шаг 2. Получить проект

Вариант А — из архива: распакуйте `password-checker.zip`, например в `C:\Projects\password-checker`. Путь лучше без кириллицы и пробелов.

Вариант Б — из GitHub: см. инструкцию 4 (клонирование в VS Code).

### Шаг 3. Запустить одним файлом

Откройте папку проекта в Проводнике → `scripts` → дважды щёлкните `run_windows.bat`.

Скрипт сам создаст виртуальное окружение `.venv`, установит библиотеки и запустит сервер. Когда увидите строку `Uvicorn running on http://127.0.0.1:8000`, откройте этот адрес в браузере.

Остановить сервер: в окне скрипта нажмите Ctrl+C, затем `Y`.

### Шаг 3 (вручную, если хотите видеть каждую команду)

Откройте «Командную строку» в папке проекта: в Проводнике щёлкните в адресную строку, наберите `cmd`, нажмите Enter.

```bat
py -3.12 -m venv .venv     # именно 3.11+; список версий: py -0
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
uvicorn app.main:app
```

Признак активного окружения — `(.venv)` в начале строки.

Режим разработки с автоперезапуском при правке кода: `uvicorn app.main:app --reload --reload-exclude "%CD%\.venv"`. Без `--reload-exclude` сервер будет бесконечно перезапускаться из-за файлов в `.venv`.

Если вы в **PowerShell**, активация — `.venv\Scripts\Activate.ps1`. При ошибке «выполнение сценариев отключено» выполните один раз:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Шаг 4. Проверить

1. http://127.0.0.1:8000 — введите `Qwerty789!`, нажмите «Проверить». Ожидается «Надёжный», «Балл: 75 из 100».
2. http://127.0.0.1:8000/health — ответ `{"status":"ok"}`.
3. Тесты — в новом окне командной строки в папке проекта:

```bat
.venv\Scripts\activate
pytest
```

Ожидается `210 passed`.

---

## macOS (Intel и Apple Silicon)

### Шаг 1. Установить Python

Откройте «Терминал» (Cmd+Пробел → «Терминал») и проверьте:

```bash
python3 --version
```

Если версия ниже 3.11 или команда не найдена — установите Python 3.12 одним из способов:

- установщик macOS с https://www.python.org/downloads/macos/ (после установки запустите `Install Certificates.command` из папки «Программы → Python 3.12»);
- или через Homebrew: `brew install python@3.12`.

Если macOS предложит установить «инструменты разработчика командной строки» — соглашайтесь, они нужны для git.

### Шаг 2. Получить проект

Распакуйте архив, например в `~/Projects/password-checker`, или клонируйте из GitHub (инструкция 3).

### Шаг 3. Запустить

```bash
cd ~/Projects/password-checker
bash scripts/run_mac.sh
```

Вручную:

```bash
python3.12 -m venv .venv      # именно 3.11+, не просто python3
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
uvicorn app.main:app
```

Остановка — Ctrl+C.

Скрипт сам найдёт Python 3.11+ (системный `python3` на macOS часто 3.9 — он не подходит) и пересоздаст `.venv`, если окружение было сделано на старой версии.

Режим разработки с автоперезапуском при правке кода:

```bash
uvicorn app.main:app --reload --reload-exclude "$PWD/.venv"
```

Без `--reload-exclude` сервер бесконечно перезапускается из-за файлов в `.venv` (особенно если проект в папке «Документы», синхронизируемой с iCloud).

### Шаг 4. Проверить

То же, что для Windows: страница, `/health`, затем в новом окне терминала:

```bash
cd ~/Projects/password-checker
source .venv/bin/activate
pytest
```

---

## Проверка API из терминала

macOS, Linux, Git Bash на Windows:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/password/check \
  -H "Content-Type: application/json" -d '{"password": "Qwerty789!"}'

curl -s -X POST http://127.0.0.1:8000/api/v1/password/generate \
  -H "Content-Type: application/json" -d '{"length": 20}'
```

Windows PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/password/check `
  -ContentType "application/json" -Body '{"password": "Qwerty789!"}'
```

В Windows PowerShell 5.1 русские тексты в ответе могут отображаться искажёнными — это особенность консоли, не приложения. Удобнее проверять через http://127.0.0.1:8000/docs (кнопка «Try it out»).

## Замер скорости (НФТ-07, БТ-08)

Сервер должен быть запущен. Во втором окне с активным окружением:

```bash
python scripts/measure_perf.py
```

## Частые проблемы

| Симптом | Причина | Что сделать |
|---|---|---|
| `python` открывает Microsoft Store | заглушка Windows | используйте `py`, или «Параметры → Приложения → Псевдонимы выполнения» → выключите python.exe |
| `'uvicorn' не является командой` | окружение не активировано | `.venv\Scripts\activate` (Windows) / `source .venv/bin/activate` (macOS) |
| `address already in use` / `[WinError 10048]` | порт 8000 занят | `uvicorn app.main:app --port 8001` и откройте http://127.0.0.1:8001 |
| `ModuleNotFoundError: No module named 'app'` | команда запущена не из корня проекта | перейдите в папку, где лежат `app/` и `requirements.txt` |
| `SSL: CERTIFICATE_VERIFY_FAILED` при `pip install` (macOS) | не установлены сертификаты | запустите `Install Certificates.command` из папки Python |
| Ошибка сборки пакета при `pip install` | слишком новая или старая версия Python | используйте Python 3.11–3.13 |
| В консоли бесконечно `WatchFiles detected changes in '.venv/...'. Reloading...` | `--reload` следит за файлами `.venv` | Ctrl+C; запускайте без `--reload` или с `--reload-exclude` (см. выше) |
| В путях ошибок видно `python3.9` | окружение создано на старом Python | `rm -rf .venv` (Windows: `rmdir /s /q .venv`) и снова скрипт запуска; при необходимости `brew install python@3.12` |
| Кнопки «Показать» и «Сгенерировать» не видны | в браузере выключен JavaScript | включите JS; без него работает только проверка, поле после неё очищается |
