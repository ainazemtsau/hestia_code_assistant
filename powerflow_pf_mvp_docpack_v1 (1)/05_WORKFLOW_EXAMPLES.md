# PowerFlow (pf): Примеры работы workflow (Codex‑first)

Дата: 2026‑03‑01  
Цель: показать **живыми сценариями**, как пользователь (не технарь) и Codex работают с pf: одна точка входа, модульность, планирование с вариантами, автономное выполнение, ревью, ретро, обновление памяти.

---

## 0) Предпосылки (MVP)

- Пользователь уже установил Codex (CLI/App).
- В репозитории добавлен pf и сгенерирован skill pack.
- Пользователь сделал **одну** команду без флагов:

```bash
pf init
```

После этого в репозитории есть `.pf/` и `.agents/skills/pf/`.

---

## 1) Сценарий A — “маленький патч” (single module)

### Шаг A1. Пользователь открывает Codex в корне проекта
Пользователь пишет в Codex:

> `$pf`

**Поведение ассистента (skill pf):**
1) Запускает:
```bash
pf status --json
```
2) Видит: миссии нет, проект idle.
3) Сухо спрашивает:

- “Опишите задачу одним предложением.”
- “Есть ли дедлайн/риски?”
- “Как проверить, что исправлено (что должно быть true)?”

Пользователь:
> “На странице checkout иногда не применяется купон. Нужно исправить. Проверка: при вводе купона скидка всегда применяется.”

### Шаг A2. Ассистент фиксирует миссию и выбирает модуль
Ассистент делает минимальный анализ структуры (через чтение файла/grep, но без “тотального документирования”) и предлагает варианты:

- Вариант A: правим только `web-checkout`
- Вариант B: правим `web-checkout` + общая библиотека `pricing`
- Вариант C: сначала подтверждаем, где баг, и только потом решаем модуль

Ассистент объясняет “почему”, затем спрашивает подтверждение. Пользователь выбирает A.

Ассистент вызывает команды pf (internal):
```bash
pf mission create --title "Fix coupon apply in checkout" --summary "...user text..."
pf module upsert --module-id web-checkout --root-path apps/web-checkout
pf task create --module-id web-checkout --title "Fix coupon apply race"
pf focus module web-checkout
```

### Шаг A3. Планирование в модуле (вместе с пользователем)
Ассистент вызывает:
```bash
pf context build --intent plan --module web-checkout --budget 6000
```

Ассистент пишет план (простым языком) + вопросы:
- “Какой источник купонов?”
- “Есть ли telemetry/логирование?”
- “Какие браузеры важны?”

Пользователь отвечает. Ассистент оформляет:

- `.pf/modules/web-checkout/PLAN.md`
- (опц.) `.pf/modules/web-checkout/SLICES.json` (если хотите allowed_paths)

И фиксирует событие:
```bash
pf artifact put --kind plan --path .pf/modules/web-checkout/PLAN.md
pf event append --type plan.drafted --scope module:web-checkout --summary "Plan drafted"
```

### Шаг A4. Ревью плана (без скриптов)
Ассистент запускает skill `pf-plan-review`:
- проверяет полноту,
- проверяет критерии проверки,
- проверяет риски,
- если чего-то не хватает — возвращает в планирование.

Пользователь подтверждает финальный план.

Ассистент:
```bash
pf event append --type plan.approved --scope module:web-checkout --summary "Plan approved by user"
pf task set-state --task-id T-001 --state EXECUTING
```

### Шаг A5. Автономное выполнение + verify + /review
Ассистент:
1) Берёт контекст:
```bash
pf context build --intent execute --module web-checkout --task T-001 --budget 8000
```
2) Делает изменения в коде.
3) Запускает тесты/линт (как определено в plan/AGENTS.md).
4) Результаты фиксирует как artifacts:
```bash
pf artifact put --kind log --path .pf/artifacts/20260301/web-checkout/pnpm-test.log
pf event append --type command.completed --summary "pnpm test ok" --payload-json '{...}'
```
5) Запускает встроенный Codex `/review` (host‑возможность), получает замечания, исправляет, повторяет verify.

### Шаг A6. Завершение + ретро + память
Ассистент сообщает пользователю:
- что сделано,
- как проверить вручную,
- какие файлы изменены,
- просит подтвердить “ок”.

После подтверждения:
```bash
pf task set-state --task-id T-001 --state DONE
pf event append --type task.completed --summary "Task done"
```

Ретро:
- ассистент задаёт 3‑5 вопросов (что пошло не так, что улучшить, что автоматизировать).
- если нашли урок (например “тесты запускаем только так”), ассистент записывает PKM:

```bash
pf pkm upsert --scope module:web-checkout --kind runbook --title "How to run checkout tests" --body-md "pnpm -C apps/web-checkout test"
pf event append --type retro.completed --summary "Retro done"
```

---

## 2) Сценарий B — “огромная задача” (multi‑module, worktrees, milestones)

Задача пользователя (нетехнический):
> “Нужно добавить поддержку Stripe + Apple Pay. Приоритет: быстрое MVP. Важно не сломать текущие платежи.”

### Шаг B1. Root intake (всё через $pf)
Пользователь:
> `$pf`

Ассистент:
1) `pf status --json`
2) задаёт вопросы “как менеджеру”:
- “Что такое MVP в 1‑2 предложениях?”
- “Какие страны/валюты?”
- “Есть ли существующий платежный провайдер?”
- “Какая метрика успеха?”
- “Какой дедлайн?”

Ассистент фиксирует миссию:
```bash
pf mission create --title "Stripe + Apple Pay MVP" --summary "...user answers..."
```

### Шаг B2. Разбиение на milestones (не планируем всё сразу)
Ассистент предлагает 3 горизонта:
- Milestone 1: минимальный платежный flow в sandbox + флаг включения
- Milestone 2: Apple Pay + UI
- Milestone 3: прод‑готовность (логирование, мониторинг, retry, docs)

Пользователь подтверждает milestone 1.

pf фиксирует milestones как artifacts:
```bash
pf artifact put --kind plan --path .pf/missions/M-0002/milestones.md
pf event append --type mission.milestones_defined --summary "3 milestones"
```

### Шаг B3. Module mapping (только затронутые модули)
Ассистент НЕ пытается документировать весь монорепо. Он ищет только по “платежам”:
- `payments-core` (backend)
- `web-checkout` (frontend)
- `infra` (секреты/деплой)

Предлагает варианты:
- A: сначала backend контракт → потом фронт
- B: фронт+backend параллельно под feature flag
- C: сначала spike в отдельной ветке

Выбираем B.

pf:
```bash
pf module upsert --module-id payments-core --root-path services/payments-core
pf module upsert --module-id web-checkout --root-path apps/web-checkout
pf module upsert --module-id infra --root-path infra
```

### Шаг B4. Worktrees (параллельные сессии)
Ассистент предлагает:
- “Создам 3 git worktree, чтобы вести параллельно и не конфликтовать. Ок?”

Если пользователь согласен:
- ассистент выполняет `git worktree add ...` (host‑инструменты)
- pf только **записывает mapping**:

```bash
pf worktree register --module-id payments-core --path ../wt-payments-core --branch feat/stripe-core
pf worktree register --module-id web-checkout --path ../wt-web-checkout --branch feat/stripe-web
pf worktree register --module-id infra --path ../wt-infra --branch feat/stripe-infra
```

Важно: pf не обязан создавать worktrees сам; достаточно хранить mapping.

### Шаг B5. Планирование на модуль (вместе с пользователем)
Для каждого модуля:
- ассистент переключается на worktree (или просто `cd`)
- вызывает `pf focus module <id>`
- вызывает `pf context build --intent plan --module <id>`

Пример по `payments-core`:
- варианты интеграции Stripe (SDK vs прямой API)
- риски idempotency и webhooks
- критерии тестов (unit + contract)

Пользователь подтверждает.

pf фиксирует планы отдельно по модулям:
- `.pf/modules/payments-core/PLAN.md`
- `.pf/modules/web-checkout/PLAN.md`
- `.pf/modules/infra/PLAN.md`

### Шаг B6. Исполнение параллельно
Ассистент запускает 3 сессии (или последовательно, но изолировано) и в каждом модуле:
- `pf context build --intent execute`
- изменение кода
- verify (тесты/линт)
- события + artifacts

Root статус показывает агрегат:
```bash
pf status
```
и сообщает блокеры:
- “web-checkout blocked until payments-core exposes endpoint /payments/intent”
- “infra blocked until keys provisioned”

### Шаг B7. Интеграционный шаг
Когда модульные задачи готовы:
- ассистент делает интеграцию (может быть отдельная задача в root или в одном модуле)
- запускает e2e, если есть

### Шаг B8. /review и релиз‑готовность milestone 1
Перед тем как сказать “готово”, ассистент:
- запускает `/review` по каждой ветке/диффу,
- собирает summary,
- проверяет docs stale (pf docs check),
- обновляет docs.

### Шаг B9. Ретро и улучшения workflow
Если выявились проблемы:
- “тесты flaky”
- “worktree неудобно создавались”
- “доки забыли обновить”

Ассистент записывает:
- incidents
- retro
- patch proposals в `.pf/local/`

---

## 3) Сценарий C — “обнаружили, что нужен другой модуль” (guardrail)

Исполнение в `payments-core`, но выяснилось, что надо поменять `pricing-lib`.

Правило:
- ассистент не имеет права молча лезть в другой модуль.

Шаги:
1) ассистент фиксирует событие:
```bash
pf event append --type dependency.uncovered --scope module:payments-core --summary "Need change in pricing-lib"
```
2) сообщает пользователю простыми словами:
- “Для решения нужно затронуть другой модуль pricing-lib. Варианты: A/B/C…”
3) если пользователь согласен:
- создаём отдельную задачу в pricing-lib
- (опционально) отдельный worktree

---

## 4) Что именно проверяем на каждом этапе (чеклист)

### После `pf init`
- `.pf/state.db` создан
- `.agents/skills/pf/` существует
- `pf status` печатает NEXT

### После root intake
- миссия создана
- есть список модулей
- root status показывает задачи

### После module planning
- PLAN.md существует и понятен человеку
- критерии проверки прописаны
- user approval зафиксирован событием

### После execution
- tests/build пройдены (есть artifacts)
- /review выполнен (есть summary)
- техдоки не stale (или обновлены)

### После retro
- есть RETRO.md
- есть минимум 1 улучшение/урок в PKM (если было что улучшать)
