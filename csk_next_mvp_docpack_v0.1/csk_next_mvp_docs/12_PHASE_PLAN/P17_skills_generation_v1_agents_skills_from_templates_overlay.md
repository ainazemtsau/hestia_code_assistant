# Phase 17 — Skills generation v1 (.agents/skills from templates + overlay)

## Objective
Реализовать генерацию skills как часть engine: `.agents/skills/` пересоздаётся детерминированно из `engine/skills_src` и `local/skills_override`.

## Deliverables
- Команда `csk skills generate`
- Generated skills в `.agents/skills/`
- Маркер “GENERATED — do not edit”

## Tasks (atomic)
- [ ] Определить простой template renderer (jinja2 optional; можно f-string).
- [ ] Скопировать engine skills_src → output, затем применить overlay overrides:
  - file override по имени
  - дополнительные файлы
- [ ] `csk bootstrap` вызывает `csk skills generate`.
- [ ] Добавить `csk validate --skills` (проверка что нет ручных правок, если нужен маркер).
- [ ] В skills каждый сценарий должен завершаться `NEXT:`.

## Validation checklist
- [ ] `csk skills generate` создаёт файлы в `.agents/skills/`
- [ ] Повторный запуск даёт идентичный результат (детерминизм)
- [ ] `csk` статус печатает подсказку что skills обновлены


