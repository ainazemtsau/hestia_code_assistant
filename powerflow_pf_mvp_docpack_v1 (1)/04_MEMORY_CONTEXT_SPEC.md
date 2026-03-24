# PowerFlow (pf): Спецификация памяти и контекста (Codex‑first, SQLite)

Дата: 2026‑03‑01  
Цель документа: снять “магичность” и описать **детерминированно**, как работает память/контекст в pf: что мы сохраняем, как избегаем мусора, как делим по модулям, как гарантируем актуальность техдоков, какие команды/скрипты для этого нужны.

---

## 0) Термины (простые)

- **Host** — конкретный AI‑инструмент: Codex CLI/App, Claude Code, Gemini CLI.
- **pf** — наш слой “данные + упаковка контекста”. pf **не рассуждает** и не “угадывает”, это делает Host‑ассистент.
- **Module** — логическая часть репозитория (папка/пакет/сервис), с собственным API и рамками изменений.
- **Worktree** — отдельный checkout репозитория (git worktree) для изоляции параллельной работы по модулю/таску.
- **Event** — короткая запись “факт произошёл” (append‑only).
- **Artifact** — файл‑доказательство/артефакт (план, логи тестов, отчёт ревью и т.д.).
- **Projection / View** — компактное состояние, вычисляемое из событий (статус/блокеры/next).
- **PKM** — полезная память (runbook/pitfalls/decisions) с доказательствами и свежестью.
- **Context Bundle** — пакет контекста для ассистента под конкретный intent (plan/execute/review/retro).

---

## 1) Принципы дизайна (жёстко)

### P1. pf = data kernel, не workflow engine
pf не пытается:
- “умно” роутить задачу по словам,
- реализовывать планирование как код,
- делать “глубокие проверки качества” вместо ассистента.

pf делает:
- хранение состояния и событий,
- хранение артефактов,
- сбор **контекст‑бандла**,
- контроль свежести (stale detection) техдоков/памяти.

### P2. Скрипты допустимы только как **детерминированные** операции над данными
Разрешено:
- CLI/скрипт “вытащи контекст по правилам”,
- CLI/скрипт “запиши событие/артефакт”,
- CLI/скрипт “проверь свежесть техдоков по fingerprint”.

Запрещено:
- “визарды”, которые пытаются угадывать архитектуру,
- самодельные LLM‑планировщики внутри pf,
- любой код, который “вместо ассистента” принимает продуктовые решения.

### P3. Никакого “сканируй весь репозиторий”
Контекст извлекается **только**:
- из выбранного scope (root/module),
- из allowed_paths (если уже есть план),
- из фиксированных “источников правды” (.pf + модульные docs).

---

## 2) Что значит “сохраняем каждый event” и почему это не мусор

### 2.1. Event — это **семантический** факт, не “каждый чих”
Мы НЕ пишем:
- “открыл файл”
- “вставил строку”
- “сделал git add”

Мы пишем только workflow‑уровень:
- создана миссия/таск,
- план создан/утверждён,
- запущена команда verify/test/build, результат ok/fail,
- выполнен ревью,
- зафиксирован инцидент,
- выполнено ретро,
- обновлена память (PKM item).

### 2.2. Большие данные не кладём в event store
- stdout/stderr тестов — отдельный artifact file (лог).
- event хранит **ссылку на artifact** + короткий summary.

### 2.3. “Много событий” превращается в полезное через 3 механизма
1) **Проекции (views)**: status/next/blockers — компактно, человек не читает сырой лог.  
2) **PKM**: выжимка фактов только из “качественных” эпизодов (успешные verify, утверждённые решения, ретро).  
3) **Context Bundles**: выборка под текущий intent и модуль, а не всё сразу.

---

## 3) Делим ли память по модулям?

Да, но правильно:

- **Event Log общий (один SQLite)** — для аудита и детерминизма.
- Каждый event обязательно имеет `scope`:
  - `scope_type = 'root'` / `scope_type = 'module'`
  - `scope_id = 'root'` или `module_id`
- **PKM и Docs — scoped**:
  - global (repo‑wide)
  - module:<id>
  - (опционально) cross:<idA>+<idB> для контрактов

Контекст под модуль:
- сперва module‑PKM + module docs,
- затем (при необходимости) global‑PKM,
- затем cross‑facts (если модуль зависит от другого).

---

## 4) Хранилище: структура файлов + SQLite

### 4.1. В репозитории создаём `.pf/`
```
.pf/
  state.db                 # SQLite (SSOT событий + views + PKM + docs)
  artifacts/               # тяжёлые артефакты: логи, отчёты
    <yyyymmdd>/...
  modules/
    <module_id>/
      MODULE.md            # краткое описание модуля (человеческое)
      KNOWLEDGE.md         # стабильные факты/runbook/pitfalls (PKM‑выгрузка)
      PLAN.md              # текущий утверждённый план (если есть)
      SLICES.json          # scope/allowed_paths (если используем)
      DECISIONS.md         # ADR‑выжимка (может быть ссылками)
      RETRO.md             # последнее ретро
      DOCS/                # docs с метаданными свежести (см. раздел 7)
  worktrees/               # (опционально) mapping; сами worktrees лежат где угодно
  local/                   # пользовательские overrides (не трогаются update)
    host/                  # codex/claude/gemini настройки
    skills_overrides/
```

### 4.2. SQLite: минимальная схема (MVP)

#### Таблица `events` (append‑only)
- `event_id INTEGER PRIMARY KEY`
- `ts TEXT` (ISO8601 UTC)
- `type TEXT` (например `task.state_changed`)
- `scope_type TEXT` (`root` | `module`)
- `scope_id TEXT` (`root` | module_id)
- `mission_id TEXT NULL`
- `task_id TEXT NULL`
- `slice_id TEXT NULL`
- `worktree_id TEXT NULL`
- `actor TEXT` (`user` | `assistant` | `pf`)
- `summary TEXT` (1 строка)
- `payload_json TEXT` (JSON)
- `artifact_ids_json TEXT` (JSON array)

Индексы:
- `(scope_type, scope_id, ts)`
- `(mission_id, task_id, ts)`
- `(type, ts)`

#### Таблица `artifacts`
- `artifact_id INTEGER PRIMARY KEY`
- `kind TEXT` (`plan` | `log` | `review` | `diff` | `handoff` | `doc`)
- `path TEXT` (relative to repo)
- `sha256 TEXT`
- `bytes INTEGER`
- `created_ts TEXT`

#### Таблица `modules`
- `module_id TEXT PRIMARY KEY`
- `root_path TEXT` (например `services/payments-core`)
- `display_name TEXT`
- `status TEXT` (optional, derived; можно хранить как кеш)
- `initialized INTEGER` (0/1) — только для UX

#### Таблица `worktrees`
- `worktree_id TEXT PRIMARY KEY`
- `module_id TEXT`
- `path TEXT`
- `branch TEXT`
- `created_ts TEXT`
- `active INTEGER`

#### Таблица `focus`
- `id INTEGER PRIMARY KEY CHECK (id=1)`
- `module_id TEXT NULL`
- `task_id TEXT NULL`
- `worktree_id TEXT NULL`

#### Таблица `pkm_items`
- `pkm_id INTEGER PRIMARY KEY`
- `scope_type TEXT` (`global`|`module`|`cross`)
- `scope_id TEXT` (`root`|module_id|“A+B”)
- `kind TEXT` (`runbook`|`pitfall`|`decision`|`convention`)
- `title TEXT`
- `body_md TEXT`
- `tags_json TEXT`
- `fingerprint_json TEXT` (см. раздел 7)
- `confidence REAL` (0..1)
- `stale INTEGER` (0/1)
- `created_ts TEXT`
- `updated_ts TEXT`

#### Таблица `pkm_sources`
- `pkm_id INTEGER`
- `source_type TEXT` (`event`|`artifact`|`file`)
- `source_ref TEXT` (event_id / artifact_id / path)
- `note TEXT`

#### Таблица `docs_index`
- `doc_id INTEGER PRIMARY KEY`
- `scope_type TEXT`
- `scope_id TEXT`
- `path TEXT`
- `sources_json TEXT` (список source‑paths/patterns)
- `fingerprint_json TEXT` (последний рассчитанный fingerprint)
- `stale INTEGER`
- `stale_reason TEXT`
- `last_checked_ts TEXT`

---

## 5) Команды/скрипты pf (минимально, но достаточно)

### 5.1. Пользовательские команды (то, что реально “видит” человек)
- `pf init`  
  Создаёт `.pf/`, `state.db`, базовые файлы, базовый skill pack для Codex.

- `pf status`  
  Печатает dashboard и **NEXT**.

- `pf focus module <module_id>`  
  Выбирает модуль в качестве текущего контекста.

(Остальные команды может вызывать ассистент; пользователь их не обязан знать.)

### 5.2. Ассистентские команды (internal API для host‑ассистента)
- `pf mission create` / `pf mission close`
- `pf module upsert` / `pf module detect`
- `pf task create` / `pf task set-state`
- `pf artifact put` (записать файл‑артефакт в `.pf/artifacts/...` и зарегистрировать)
- `pf event append` (универсально)
- `pf pkm upsert` / `pf pkm list`
- `pf docs scan` / `pf docs check` / `pf docs mark-fixed`
- `pf context build --intent <plan|execute|review|retro|status> [--module ...] [--task ...] [--budget ...]`
- `pf replay --check` (детерминизм и целостность)

---

## 6) Context Builder: как **детерминированно** выдаём “нужные куски” и не сканируем всё

### 6.1. Входные параметры
`pf context build` принимает:
- `intent`: `plan|execute|review|retro|status`
- `scope`: root или module (явно или из `focus`)
- `module_id`, `task_id` (если применимо)
- `budget`: (байты/токены) для контента
- `query`: (опционально) ключевые слова от ассистента/пользователя
- `allowed_paths`: (если в SLICES.json есть) иначе вычисляем из module root

### 6.2. Алгоритм сборки (MVP, без магии)
1) Определить **рабочий scope**:
   - если `--module` указан → module scope
   - иначе если `focus.module_id` установлен → module scope
   - иначе → root scope

2) Определить **allowed roots**:
   - если есть `SLICES.json` и текущий slice известен → allowed_paths из него
   - иначе allowed_paths = `modules.root_path` (одна папка)

3) Собрать **обязательные документы**:
   - `.pf/modules/<module>/PLAN.md` (если есть)
   - `.pf/modules/<module>/KNOWLEDGE.md` (если есть)
   - `.pf/modules/<module>/DECISIONS.md` (если есть)
   - root `AGENTS.md` + module `AGENTS.md` (важно для Codex, но это скорее host‑уровень)

4) Собрать **последние события** по типам (ограниченно):
   - последние 20 `command.*` (особенно fail)
   - последние 20 `task.*`/`plan.*`
   - последние 10 `incident.*`
   - последние 10 `doc.*` (stale/fixed)

5) Собрать **PKM**:
   - `pkm_items` где `scope=module` и `stale=0` (топ N по `confidence`)
   - затем `scope=global` (топ M)
   - затем cross (если явно указаны зависимости)

6) Собрать **кодовые фрагменты**:
   - Источник сигналов:
     - `query` (если есть)
     - названия файлов/символов из PLAN/SLICES (регекс‑экстракция)
     - последние error строки из verify logs (если есть)
   - Технически:
     - `rg` (ripgrep) запускается **только внутри allowed_paths**
     - выбираем top K файлов по количеству/качеству совпадений
     - для каждого файла берём не весь файл, а “окна” ±N строк вокруг совпадений
   - Ограничения:
     - не более K файлов (например 8)
     - не более W окон на файл (например 3)
     - не более B байт всего (budget)

7) Сгенерировать **freshness report** (см. раздел 7):
   - stale docs list
   - stale PKM items (если их всё равно включили — то с пометкой)

8) Выдать результат:
   - `bundle.json` (машиночитаемо)
   - `bundle.md` (читаемо)

### 6.3. Что важно: ассистент **обязан** использовать `pf context build`
Чтобы не было “каждый раз по‑разному”:
- в SKILL.md фиксируем правило: перед планированием/исполнением/ревью сначала вызвать `pf context build`.

---

## 7) Актуальность техдоков: как гарантируем “docs всегда свежие”

### 7.1. Документ ≠ “просто текст”. Документ имеет контракт источников
Любой “технический документ”, который должен быть актуальным (API contract, архитектура модуля), создаётся с метаданными:

Пример в начале файла `.pf/modules/payments-core/DOCS/API.md`:
```yaml
---
pf_doc:
  scope: module:payments-core
  sources:
    - path: services/payments-core/src/api/
      mode: git-tree
    - path: services/payments-core/openapi.yaml
      mode: file-sha
  freshness:
    policy: strict
    stale_on_any_change: true
---
```

### 7.2. Fingerprint: что это и как считается (детерминированно)
Для каждого источника считаем fingerprint:
- `file-sha`: sha256 содержимого файла
- `git-tree`: git tree hash директории (быстро, без чтения всех файлов)
- `glob`: список файлов + их git blob hashes (если нужно)

Суммарный fingerprint документа = хеш от набора fingerprints источников.

### 7.3. pf docs check
Команда:
- читает `pf_doc` метаданные всех docs
- пересчитывает fingerprints
- если изменилось → `docs_index.stale=1` и событие `doc.stale_detected`

### 7.4. Как stale doc попадает в поведение ассистента
- `pf status` показывает “Docs stale: N”
- `pf context build` включает freshness report
- SKILL “pf-review” (или “pf-execute”) имеет правило:  
  **если stale docs затронуты текущим планом/файлами — обновить docs как часть работы**.

Это не “тысяча проверок”, это один детерминированный механизм stale‑детекта.

---

## 8) PKM (полезная память): как она создаётся и обновляется

### 8.1. PKM items — только из контрольных точек
Мы не создаём PKM на каждом шаге. Триггеры:
- после `plan.approved` (фиксируем “intent и рамки”)
- после успешного `verify ok` (фиксируем runbook команд)
- после `retro.completed` (фиксируем pitfalls и улучшения)
- после “важного решения” (ADR/decision)

### 8.2. Кто пишет текст PKM?
Ассистент (Codex) — потому что это смысл и язык.

pf только:
- сохраняет,
- связывает с источниками,
- отмечает stale по fingerprint,
- отдаёт в context bundle.

### 8.3. Как PKM становится stale
PKM item содержит `fingerprint_json` (те же источники, что и docs).
Если источники изменились:
- `stale=1`
- событие `pkm.stale_detected`
- context builder либо:
  - не включает item,
  - либо включает с пометкой “stale, needs revalidation”.

---

## 9) Состояния (states) и что память делает в каждом

Ниже — не “кодовый FSM”, а **операционные состояния**, которые мы поддерживаем данными.

### 9.1. State: UNINITIALIZED
Условия:
- нет `.pf/state.db`

Поведение:
- `pf`/`pf status` пишет “не инициализировано” и NEXT = `pf init`.
- никаких событий (кроме опционального `pf.invoked_uninitialized`).

### 9.2. State: INITIALIZED + IDLE
Условия:
- `.pf/state.db` есть
- нет активной миссии

Поведение:
- `pf status` показывает: modules list, docs stale counters, last events.
- NEXT = “создать миссию/задачу” (в Codex это будет интерактивно через skill; pf даёт команду `pf mission create` как следующий шаг ассистенту).

Память:
- можно обновлять module registry
- можно проверять stale docs

### 9.3. State: MISSION_ACTIVE (root)
Условия:
- есть миссия `M-*` в статусе ACTIVE

Поведение:
- root dashboard агрегирует:
  - какие модули задействованы
  - какие задачи в каких состояниях
  - блокеры

Память:
- события про миссию/задачи пишутся в `events`
- `pf context build --intent status` даёт короткий обзор для ассистента “как менеджеру”.

### 9.4. State: MODULE_PLANNING (module)
Условия:
- task в модуле в состоянии `PLANNING`

Поведение:
- ассистент вызывает `pf context build --intent plan --module X`
- пишет `.pf/modules/X/PLAN.md` + (опц.) `SLICES.json`
- создаёт событие `plan.drafted`
- просит пользователя подтвердить
- затем вызывает ревью‑skill (в Codex это может быть отдельный агент/skill, не скрипт)

Память:
- план = artifact (фиксируем path + sha)
- решения = `.pf/modules/X/DECISIONS.md` (при необходимости)
- `docs check` можно запускать до/после, чтобы видеть stale.

### 9.5. State: MODULE_EXECUTING (module)
Условия:
- plan approved
- task.state = EXECUTING

Поведение:
- ассистент вызывает `pf context build --intent execute`
- делает изменения в пределах module scope
- запускает тесты/сборку (host‑инструменты)
- результаты фиксирует как:
  - artifacts (логи)
  - events `command.completed`
- по завершении — `/review` в Codex (host‑фича), плюс сохраняет review summary как artifact.

Память:
- runbook команды (тест/линт) добавляются в PKM (если полезно)
- доки проверяются stale‑детектором; если stale и затронуты — обновляются.

### 9.6. State: MODULE_READY / DONE
Условия:
- ассистент считает работу завершённой
- пользователь подтвердил (или согласован процесс)

Поведение:
- ассистент обновляет status
- предлагает ретро

Память:
- `retro.completed` → создаём pitfalls/улучшения в PKM
- патчи workflow — только в `.pf/local/` (overrides)

---

## 10) Интеграция с Codex (почему это будет удобно)

1) **Skills (SKILL.md) с progressive disclosure**: Codex сначала загружает только метаданные skills (name/description) и читает полный SKILL.md только при активации, что помогает держать набор навыков большим без раздувания контекста.  
2) **AGENTS.md цепочка root‑to‑leaf**: правила можно держать глобально в корне, а модульные уточнения — рядом с модулем. Host сам подмешивает их в правильном порядке.  
3) `/review` — встроенный быстрый workflow для ревью изменений.

pf под Codex не должен “перепридумывать” эти механики — мы их используем.

---

## 11) Минимальные skills (концептуально)

- `pf` (root router): всегда стартует со `pf status --json`, затем спрашивает пользователя (вежливо, сухо), затем вызывает нужные internal команды pf.
- `pf-plan`: планирование под модуль (варианты A/B/C, вопросы, PLAN.md).
- `pf-plan-review`: критик плана (LLM‑ревью, не скрипт).
- `pf-exec`: исполнение (использует `pf context build`, затем правит код, запускает тесты, /review).
- `pf-retro`: ретро и обновление PKM + предложение patch в `.pf/local`.

---

## 12) “Границы модулей” без тысячи проверок

Мы делаем это инструкцией + контекстом:
- Контекст выдаётся только для текущего модуля (allowed_paths = module root).
- Skill запрещает менять файлы вне scope.
- Если во время работы обнаружено, что нужен другой модуль:
  - ассистент фиксирует “dependency uncovered” как event
  - возвращается к root, предлагает создать отдельную задачу в новом модуле

Опционально (позже): можно добавить лёгкий `pf diff scope-check` как подсказку (не как строгий блокер).

---

## 13) Пример выходного `pf status` (ожидаемый формат)

### IDLE
```
Project: OK
Active mission: none
Modules: 3 (payments-core, web-checkout, infra)

Docs stale:
- payments-core: 1 (API.md)
- web-checkout: 0
- infra: 0

NEXT: Describe the task in Codex using $pf (or run: pf mission create)
```

### Module executing
```
Mission: M-0042 "Payments v2"
Module: payments-core
Task: T-010 "Add idempotency key support"
State: EXECUTING
Last verify: ok (pnpm test) 3m ago
Docs stale: 1 (API.md)

NEXT: pf context build --intent execute --module payments-core
```

---

## 14) Что считается “готово” для памяти в MVP

1) `pf context build` выдаёт bundle, который:
- не сканирует весь репо,
- детерминированно выбирает источники,
- содержит freshness report,
- работает в module scope.

2) `pf docs check` реально помечает stale docs при изменении sources.

3) PKM items:
- можно добавить/прочитать,
- stale меняется при изменении fingerprint источников,
- context builder включает только fresh (или помечает stale).

4) Вся логика не зависит от LLM “магии” — LLM лишь пишет текст планов/ретро/PKM.

---

## 15) Следующие расширения (после MVP)
- MCP server поверх тех же операций (tools/resources/prompts), чтобы Claude/Gemini подключались как клиенты.
- Более умный retrieval (дерево символов, LSIF), но только после того как детерминированный базовый контур доказан.
