# PHASE 01 — Event Log + Artifacts (append-only + pointers)

## Цель фазы
Сделать так, чтобы pf мог:
- писать события (`pf event append`)
- регистрировать артефакты (файлы) (`pf artifact put`)
- безопасно хранить большие данные вне SQLite (логи, bundle, review)

Это основа “памяти”: ассистент фиксирует факты, но не заливает мегабайты в БД.

---

## Deliverables

### Команды
- `pf event append ...`
- `pf event tail [--scope ...] [--limit N] [--json]`
- `pf artifact put --kind ... --path ...`

### Код
- `pf/events.py`
- `pf/artifacts.py`

### Tests
- `tests/test_events.py`
- `tests/test_artifacts.py`

---

## Реализация (пошагово)

### 1) `pf artifact put`
Поведение:
- вход: `--kind` (строка), `--path` (repo-relative)
- проверка: файл существует
- вычислить `sha256`, `bytes`
- вставить в таблицу `artifacts`
- вернуть `artifact_id`

Вывод:
- human: `ARTIFACT OK id=<id> kind=<kind> path=<path> sha256=<short>`
- json: `{ok:true, artifact:{artifact_id,...}}`

### 2) `pf event append`
Входы:
- `--type`
- `--scope-type` root|module
- `--scope-id` root|<module_id>
- `--summary`
- `--actor` user|assistant|pf (по умолчанию assistant)
- `--payload-json '{...}'` или `--payload @file.json`
- `--artifact-ids '1,2,3'` (опционально)

Поведение:
- вставить строку в `events`
- вернуть `event_id`
- не делать никакой “логики” поверх (это сырьё)

### 3) `pf event tail`
- показать последние N событий (по умолчанию 20)
- фильтры:
  - `--scope-type module --scope-id X`
  - `--mission-id ...` (опционально)
- в human режиме печатать: ts type scope summary

---

## Acceptance (ручная проверка)

1) Создать файл `tmp.log` и зарегистрировать:
```bash
echo "hello" > tmp.log
./pf artifact put --kind log --path tmp.log
```

2) Добавить событие:
```bash
./pf event append --type command.completed --scope-type root --scope-id root \
  --summary "demo command ok" --payload-json '{"cmd":"echo hello","exit_code":0}' \
  --artifact-ids "1"
```

3) Посмотреть tail:
```bash
./pf event tail --limit 5
```
Ожидаемо: события видны, артефакт зарегистрирован.

---

## Tests

- append event → row count увеличился
- artifact put → sha256 корректный
- tail returns ordered by ts DESC (или event_id DESC)

---

## Non-goals

- вычисление status/next из событий
- контекст бандлы
