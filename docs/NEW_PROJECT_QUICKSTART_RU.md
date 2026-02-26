# Полный старт CSK в новом проекте (от GitHub до push)

Ниже полный путь: скачать проект, поднять окружение, запустить workflow и вести работу до отправки в GitHub.

## 1. Предусловия

- `git`
- `python` версии `>=3.12` (важно: `./csk` вызывает именно `python`)
- `bash` (Linux/macOS или WSL)

Проверка:

```bash
git --version
python --version
```

## 2. Скачать проект из GitHub

```bash
git clone https://github.com/ainazemtsau/hestia_code_assistant.git
cd hestia_code_assistant
```

## 3. Подготовить окружение (рекомендуется)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Если не хотите ставить пакет в editable-режиме, можно работать через `./csk` без установки, но `python` всё равно должен быть `3.12+`.

## 4. Первый запуск workflow

```bash
./csk status --json
./csk bootstrap
./csk skills generate
./csk status --json
```

Ожидаемо:
- `status: ok`
- `skills.status: ok`
- рекомендация `next.recommended` обычно `csk run`

## 5. Создать первую рабочую задачу

```bash
./csk new "Опиши первую задачу продукта" --modules root
./csk run
```

Дальше всегда идите по `NEXT`, который возвращает `csk`.

## 6. Базовый рабочий цикл (каждый task)

```bash
./csk new "Implement feature X" --modules root
./csk run
./csk approve --module-id root --task-id T-0001 --approved-by <your_name>
./csk run
./csk retro --module-id root --task-id T-0001
./csk replay --check
```

## 7. Ежедневный старт работы

```bash
source .venv/bin/activate
git pull --rebase
./csk status --json
./csk run
```

## 8. Обязательные проверки перед push

```bash
./csk validate --all --strict --skills
./csk replay --check
./csk doctor run --git-boundary
```

Все команды должны завершаться со `status: ok`.

## 9. Отправка изменений в GitHub

```bash
git checkout -b feat/<short-name>
git add .
git commit -m "feat: <what changed>"
git push -u origin feat/<short-name>
```

После push откройте PR в GitHub.

## 10. Если что-то сломано

Выполняйте строго по порядку:

```bash
./csk status --json
./csk skills generate
./csk validate --all --strict --skills
./csk replay --check
./csk doctor run --git-boundary
```

Если в `status --json` видно `skills.status=failed`, первая команда всегда:

```bash
./csk skills generate
```

## 11. Важные правила

- Используйте user-facing команды: `csk`, `csk new`, `csk run`, `csk approve`, `csk module <id>`, `csk retro`.
- Не редактируйте `.agents/skills/` вручную; используйте `./csk skills generate`.
- Локальные кастомизации храните в `.csk/local/`.
