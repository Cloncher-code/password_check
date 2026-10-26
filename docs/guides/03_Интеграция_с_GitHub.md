# Инструкция 3. Интеграция проекта с GitHub

Для кого: Андрей (владелец репозитория) и Марина (участник). Время: 20–30 минут.

Результат: код в репозитории GitHub, у Марины есть доступ, тесты запускаются автоматически на Windows, macOS и Linux при каждом push, версия `v1.0` помечена тегом.

Настройка git и VS Code на Windows подробно — в инструкции 4. Здесь — что делается на GitHub и в терминале на любой ОС.

## 1. Аккаунты

1. Каждый участник регистрируется на https://github.com (Sign up).
2. Включите двухфакторную аутентификацию: аватар → Settings → Password and authentication → Enable two-factor authentication. GitHub её требует для отправки кода.

## 2. Создать репозиторий (Андрей)

1. https://github.com/new
2. Repository name: `password-checker`.
3. Видимость: Private (виден только приглашённым) или Public. О разнице — в разделе 6.
4. **Не** ставьте галочки «Add a README», «.gitignore», «license» — они уже есть в проекте, иначе при первой отправке будет конфликт.
5. Create repository. Оставьте страницу открытой: понадобится адрес вида `https://github.com/<логин>/password-checker.git`.

## 3. Первая отправка кода (Андрей)

Проще всего через VS Code (инструкция 4, раздел 5: «Publish to GitHub»). Через терминал, из папки проекта:

```bash
git init
git add .
git commit -m "v1.0: код, тесты, документация"
git branch -M main
git remote add origin https://github.com/<логин>/password-checker.git
git push -u origin main
```

При первом `git push` откроется окно входа в GitHub (Git Credential Manager). На macOS, если окно не появилось, установите GitHub CLI (`brew install gh`) и выполните `gh auth login`.

Проверьте: на странице репозитория видны папки `app`, `docs`, `tests` и README.

## 4. Автотесты (GitHub Actions)

В проекте уже есть `.github/workflows/tests.yml`. После первого push:

1. Вкладка **Actions** → запуск «tests». 6 задач: Windows, macOS, Linux × Python 3.11 и 3.13.
2. Зелёная галочка — всё прошло. Красный крестик — откройте задачу, раскройте упавший шаг, там текст ошибки.

Тесты запускаются на каждый push и pull request. Это и есть проверка «работает на Windows и Mac» без ручного запуска на каждой машине.

## 5. Пригласить Марину (Андрей)

Settings → Collaborators → Add people → логин Марины → Add. Марина принимает приглашение из письма или на https://github.com/notifications.

## 6. Защитить ветку main (рекомендуется)

Settings → Branches → Add branch ruleset (или Add classic branch protection rule) для `main`:

- Require a pull request before merging, Required approvals: 1;
- Require status checks to pass → выберите проверки `test (...)` из workflow «tests».

Тогда в `main` попадает только код, прошедший ревью и тесты, — это и есть DoD из файла 06.

Важно: на бесплатном тарифе GitHub правила защиты веток для **приватных** репозиториев, насколько мне известно, недоступны. Варианты: сделать репозиторий публичным (в коде нет секретов) или договориться о правиле «только через pull request» без технической защиты. Проверьте актуальные условия в разделе Settings → Branches вашего репозитория.

## 7. Рабочий процесс: задача → ветка → pull request

1. Задача из бэклога заводится как **Issue**: вкладка Issues → New issue, заголовок `T-05 Штрафы P1, P2`, в тексте — требования и критерий готовности.
2. Разработчик создаёт ветку под задачу:

```bash
git switch main
git pull
git switch -c feature/T-05-penalties
```

3. Работает, коммитит маленькими шагами, с ID требований в сообщении:

```bash
git add app/scoring.py tests/test_scoring.py
git commit -m "БП-03: штраф P2 без перехода 9→0 (T-05)"
git push -u origin feature/T-05-penalties
```

4. На GitHub появится кнопка **Compare & pull request**. В описании заполните шаблон (он подставится сам) и напишите `Closes #<номер issue>`.
5. Ревьюер (Андрей как СА) смотрит вкладку «Files changed», оставляет комментарии, нажимает Review → Approve.
6. Когда тесты зелёные и есть одобрение → **Merge pull request** → Delete branch. Issue закроется сам.

## 8. Общая скрам-доска в GitHub

Вкладка **Projects** → New project → шаблон «Board». Колонки переименуйте: «Бэклог», «К работе», «В работе», «На проверке», «Готово». Добавьте issues T-01…T-24. Поле «Iteration» — спринты, поле «Estimate» — SP, метка `⛔ блокер` — для вопросов аналитику.

Такая доска общая для Андрея и Марины без дополнительных настроек; это вариант к `docs/BOARD.md`.

## 9. Выпуск версии v1.0

После подписанного протокола UAT:

```bash
git switch main
git pull
git tag -a v1.0 -m "Версия 1.0: UAT пройден"
git push origin v1.0
```

На GitHub: Releases → Draft a new release → тег `v1.0` → описание (что входит, ссылка на протокол UAT) → Publish release. GitHub сам приложит архив исходников.

## 10. Что не должно попасть в репозиторий

Файл `.gitignore` уже исключает `.venv/`, `__pycache__/`, `.coverage`, `.env`. Никогда не коммитьте пароли, токены и ключи. Если это случилось — удаления файла недостаточно, ключ надо считать скомпрометированным и выпустить новый.

## Частые проблемы

| Симптом | Что сделать |
|---|---|
| `remote: Permission to ... denied` / 403 | вы вошли не тем аккаунтом. Windows: «Диспетчер учётных данных» → «Учётные данные Windows» → удалить `git:https://github.com` → push снова. macOS: «Связка ключей» → удалить запись github.com |
| `! [rejected] main -> main (fetch first)` | на GitHub есть изменения, которых нет у вас: `git pull --rebase`, затем `git push` |
| `src refspec main does not match any` | не было ни одного коммита: сделайте `git commit` |
| `Author identity unknown` | `git config --global user.name "Имя"` и `git config --global user.email "почта@из.github"` |
| Конфликт при pull/merge | откройте файл в VS Code: он покажет «Accept Current / Incoming / Both»; выберите, сохраните, `git add`, `git commit` |
