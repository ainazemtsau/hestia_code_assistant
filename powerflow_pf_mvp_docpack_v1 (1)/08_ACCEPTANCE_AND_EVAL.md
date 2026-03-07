# 08 — Acceptance и регрессии (MVP)

## 0) Почему это важно

В прошлых итерациях “платформа зелёная”, но end-to-end не доказан.
В этом MVP успех определяется **только** прохождением acceptance сценариев.

---

## Acceptance A — Greenfield (single-module patch)

Цель: доказать, что pf даёт:
- init одной командой,
- status+next,
- модульную память,
- контекст для планирования/выполнения/ревью,
- обновление docs/PKM/retro.

### Шаги
1) В новом репозитории:
   - скопировать pf (или добавить как подмодуль)
   - выполнить `./pf init`
2) Открыть Codex в корне repo.
3) Ввести задачу (пример): “Добавь endpoint /health и тест”.
4) Ассистент:
   - вызывает `pf status --json`
   - создаёт module `app` (если нужно)
   - делает план (A/B/C)
   - пишет `.pf/modules/app/PLAN.md`
   - просит подтверждение плана
   - выполняет изменения
   - запускает тесты
   - делает `/review`
   - выдаёт отчёт
   - запускает ретро и обновляет KNOWLEDGE.md / PKM

### Проверки (обязательные артефакты)
- `.pf/state.db` существует и содержит события:
  - `pf.init.completed`
  - `mission.created`
  - `task.created`
  - `plan.saved`
  - `plan.approved`
  - `command.completed` (tests)
  - `review.completed`
  - `retro.completed`
- `.pf/modules/app/PLAN.md` существует
- `.pf/modules/app/KNOWLEDGE.md` существует и содержит команды verify
- `.pf/artifacts/bundles/*.json` существует (минимум 2: plan + execute)
- `pf docs check` не показывает stale docs (или показывает и ассистент фиксит)
- `pf status` после завершения показывает “idle” и NEXT = “введите новую задачу”

---

## Acceptance B — Big task (multi-module + milestone-1)

Цель: доказать, что огромная задача не превращается в “сделаем всё сразу”, а режется.

### Шаги
1) Задача: “Добавить оплату: backend + frontend + infra; в итоге простая демка”.
2) Ассистент:
   - фиксирует mission + milestones (только milestone-1 детально)
   - предлагает 2–3 варианта разбиения по модулям
   - создаёт 2–3 модуля (например backend/web/infra)
   - создаёт tasks на milestone-1
   - работает модульно (не лезет в другие модули без явного согласия)

### Проверки
- в SQLite есть минимум 2 module_id кроме root
- `pf status` показывает progress по модулям
- `pf context build` в модуле A не тянет чужие файлы

---

## Регрессии (должны быть автоматизированы в tests/)

1) `pf init` идемпотентен
2) schema migrations работают
3) `pf status --json` всегда валиден и содержит next.cmd
4) `pf context build` всегда bounded budget и respects allowed_paths
5) docs freshness: изменение source → doc stale = 1
