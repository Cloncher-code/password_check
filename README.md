# Проверка сложности пароля

Веб-приложение и API: оценивает надёжность пароля по правилам СТ v1.0, даёт рекомендации и генерирует надёжные пароли. Пароли нигде не сохраняются.

Стек: Python 3.11+, FastAPI, Uvicorn, Jinja2, HTML5, CSS, чистый JS. Без базы данных и внешних сервисов.

## Быстрый старт

| ОС | Команда из папки проекта |
|---|---|
| Windows | двойной щелчок по `scripts\run_windows.bat` |
| macOS / Linux | `bash scripts/run_mac.sh` |

Откройте http://127.0.0.1:8000. Подробно, с ручной установкой и решением проблем — [docs/guides/01_Запуск_локально_Windows_macOS.md](docs/guides/01_Запуск_локально_Windows_macOS.md).

Вручную (нужен Python 3.11+, проверка: `python --version`):

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app
```

## API

Интерактивная документация: http://127.0.0.1:8000/docs (страница подгружает свои скрипты из интернета).

| Метод | Адрес | Что делает |
|---|---|---|
| POST | `/api/v1/password/check` | оценка пароля |
| POST | `/api/v1/password/generate` | генерация пароля (длина 12–64, по умолчанию 16) |
| GET | `/health` | проверка, что сервис жив |

Проверка пароля (macOS, Linux, Git Bash):

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/password/check \
  -H "Content-Type: application/json" \
  -d '{"password": "Qwerty789!"}'
```

Windows PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/password/check `
  -ContentType "application/json" -Body '{"password": "Qwerty789!"}'
```

Ответ: `score` (0–100), `level` (`WEAK` / `MEDIUM` / `STRONG` / `VERY_STRONG`), `level_label`, `checks`, `penalties`, `recommendations`. Ошибки — HTTP 422 и `{"error": {"code": "...", "message": "..."}}`. Полный контракт — СТ §6.

Встраивание в свою форму регистрации (JS):

```js
const r = await fetch("http://127.0.0.1:8000/api/v1/password/check", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ password: input.value }),
});
const data = await r.json();   // data.level_label, data.recommendations
```

Если форма открыта с другого адреса, браузер заблокирует запрос (CORS). Настройка CORS в MVP не входит — см. руководство разработчика, раздел «Как расширить».

## Тесты

```bash
pytest                              # 207 тестов
pytest --cov=app                    # покрытие (требование ≥ 90 %)
python scripts/build_reference.py   # Приложение А: ожидание = код
python scripts/measure_perf.py      # замер скорости на запущенном сервере
```

## Структура

```
app/            код: main.py (роуты), scoring.py (оценка), generator.py, config.py (все правила), schemas.py
templates/      HTML-страница (Jinja2)
static/         CSS и JS
tests/          тесты; reference_set.py — эталонный набор (Приложение А)
scripts/        запуск, пересчёт Приложения А, замер скорости
docs/           БТ, СТ, отчёты QC, тест-план, UAT, инструкции
```

## Документация

Оглавление всех документов по этапам — [docs/README.md](docs/README.md).

| Документ | Файл |
|---|---|
| Бизнес-требования | `docs/БТ_Пароль_v1.0.md` / `.docx` |
| Спецификация требований | `docs/СТ_Пароль_v1.0.md` / `.docx` |
| Запуск на Windows и macOS | `docs/guides/01_Запуск_локально_Windows_macOS.md` |
| Руководство разработчика | `docs/guides/02_Руководство_разработчика.md` |
| Интеграция с GitHub | `docs/guides/03_Интеграция_с_GitHub.md` |
| GitHub в VS Code на Windows | `docs/guides/04_GitHub_в_VS_Code_Windows.md` |
