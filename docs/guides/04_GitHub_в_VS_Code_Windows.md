# Инструкция 4. Настройка GitHub в VS Code на Windows

Для кого: разработчик на Windows 10/11 (Марина). Время: 20 минут.

Результат: VS Code связан с вашим аккаунтом GitHub, проект склонирован, запускается и отлаживается; вы умеете сделать ветку, коммит, push и pull request, не выходя из VS Code.

## 1. Установить Git для Windows

1. Скачайте с https://git-scm.com/download/win (64-bit Git for Windows Setup) или выполните в «Командной строке»: `winget install --id Git.Git -e`.
2. В установщике оставляйте значения по умолчанию, кроме трёх экранов:
   - «Choosing the default editor used by Git» → **Use Visual Studio Code as Git's default editor**;
   - «Adjusting the name of the initial branch» → **Override… → main**;
   - «Choose a credential helper» → **Git Credential Manager** (по умолчанию так и есть).
3. Проверьте в новом окне командной строки: `git --version`.

## 2. Представиться git (один раз)

```bat
git config --global user.name "Марина Иванова"
git config --global user.email "почта-как-в-github@example.com"
```

Почта должна совпадать с почтой в GitHub (Settings → Emails), иначе коммиты не привяжутся к аккаунту. Если хотите скрыть почту — возьмите адрес вида `12345+login@users.noreply.github.com` там же.

Окончания строк в проекте фиксирует файл `.gitattributes`, дополнительно ничего настраивать не нужно.

## 3. Установить VS Code и расширения

1. https://code.visualstudio.com/ или `winget install --id Microsoft.VisualStudioCode -e`. В установщике отметьте «Добавить в PATH» и «Открыть с помощью Code» в контекстном меню.
2. Расширения (Ctrl+Shift+X): **Python** (Microsoft) — подтянет Pylance и Python Debugger; **GitHub Pull Requests**; **GitHub Actions**. Когда вы откроете проект, VS Code сам предложит их установить (файл `.vscode/extensions.json`).
3. Python установлен по инструкции 1.

## 4. Войти в GitHub из VS Code

1. Значок человечка (Accounts) в левом нижнем углу → **Sign in with GitHub to use GitHub Pull Requests**.
2. Откроется браузер → Authorize Visual Studio Code → вернитесь в VS Code.
3. При первом push git может ещё раз открыть окно входа (Git Credential Manager) — войдите тем же аккаунтом.

## 5. Получить проект

**Если репозиторий уже есть на GitHub (Марина):**

1. Ctrl+Shift+P → «Git: Clone» → «Clone from GitHub» → выберите `password-checker`.
2. Укажите папку, например `C:\Projects` (без кириллицы и пробелов). → Open.

**Если код только в архиве и репозитория ещё нет (Андрей):**

1. File → Open Folder → папка распакованного проекта.
2. Панель Source Control (Ctrl+Shift+G) → **Publish to GitHub** → выберите Private или Public → отметьте все файлы → OK.
3. VS Code сам сделает `git init`, первый коммит, создаст репозиторий и отправит код. Затем — инструкция 3, разделы 4–6.

## 6. Подготовить Python в VS Code

1. Terminal → New Terminal (Ctrl+`).
2. Чтобы не столкнуться с ошибкой PowerShell «выполнение сценариев отключено», выберите командную строку: стрелка рядом с «+» в панели терминала → **Select Default Profile** → **Command Prompt**. Откройте новый терминал.
3. Создайте окружение и поставьте зависимости:

```bat
py -3.12 -m venv .venv     # именно 3.11+; список версий: py -0
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

4. Ctrl+Shift+P → «Python: Select Interpreter» → `.\.venv\Scripts\python.exe`.
5. Проверка: колба слева (Testing) → «Run Tests» → 210 зелёных. F5 → «Запустить сервер (uvicorn, отладка)» → http://127.0.0.1:8000.

## 7. Ежедневная работа

| Действие | Где в VS Code | То же командой |
|---|---|---|
| Забрать свежий код | нижняя панель: значок ⟳ (Synchronize) | `git pull` |
| Новая ветка под задачу | клик по имени ветки слева внизу → «Create new branch» → `feature/T-05-penalties` | `git switch -c feature/T-05-penalties` |
| Посмотреть изменения | Source Control → щелчок по файлу (откроется сравнение) | `git diff` |
| Подготовить файлы | «+» у файла (Stage) | `git add файл` |
| Коммит | поле Message → «Commit» (Ctrl+Enter) | `git commit -m "..."` |
| Отправить | «Publish Branch» / «Sync Changes» | `git push` |
| Pull request | значок GitHub слева → «Create Pull Request» | — |
| Статус тестов на GitHub | значок GitHub Actions слева | — |

Сообщение коммита — с ID требования и задачи: `БП-03: штраф P2 без перехода 9→0 (T-05)`.

## 8. Pull request из VS Code

1. После push: панель GitHub Pull Requests → «Create Pull Request».
2. Base: `main`, Compare: ваша ветка. Заполните шаблон, добавьте `Closes #5`, Reviewers: Андрей → Create.
3. Комментарии ревьюера появляются прямо в коде в VS Code. Исправьте, закоммитьте, сделайте push — PR обновится сам.
4. После одобрения и зелёных тестов: Merge в панели PR (или на сайте). Затем переключитесь на `main` и сделайте Sync.

## Частые проблемы

| Симптом | Что сделать |
|---|---|
| VS Code не видит git: «Git not found» | перезапустите VS Code после установки Git; проверьте `git --version` в новом терминале |
| Push просит логин и пароль, пароль не подходит | GitHub не принимает пароль аккаунта для git. Обновите Git for Windows — Git Credential Manager откроет вход через браузер |
| 403 / Permission denied | «Диспетчер учётных данных Windows» → «Учётные данные Windows» → удалите `git:https://github.com` → push снова |
| Предупреждение `LF will be replaced by CRLF` | безопасно, это `.gitattributes` выравнивает окончания строк |
| Тесты не видны во вкладке Testing | не выбран интерпретатор `.venv` (шаг 6.4) или не установлен pytest (`pip install -r requirements-dev.txt`) |
| «Publish to GitHub» не предлагает репозиторий | не выполнен вход (раздел 4) |
