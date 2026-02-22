# CSK‑Next (Codex‑only) — Фазовая спецификация workflow (для dev team)

Версия: **draft v0.1**  
Дата: **2026‑02‑20**  
Автор: ChatGPT (по требованиям пользователя)  

## 0) Контекст и цель документа

Этот документ — **полное и исполнимое (по смыслу) описание фаз** нового workflow “CSK‑Next” **без внешних платформ** (Temporal/трекеры/CI — опциональны), рассчитанного на **solo‑разработку** с Code Assistant (Codex/Claude/etc).

Dev team должен:
- реализовать **ядро** (engine) и **контракты артефактов**;
- реализовать **минимальный CLI**, который обеспечивает enforce‑переходы между фазами;
- реализовать **skills** и структуру инструкций так, чтобы UX был “одна точка входа, дальше ведём пользователя”.

Пользователь:
- активно участвует **только в планировании и approve‑чекпойнтах**;
- git‑операции (commit/push/merge) на первом этапе выполняет сам.

---

## 1) North Star (как должно ощущаться пользователю)

**Сценарий “пришёл в root с задачей”:**
1) Пользователь запускает **одну команду**: `$csk` (или `$control-tower` как alias).
2) Ассистент сам:
   - понимает масштаб задачи (1 модуль / много модулей / неясно),
   - предлагает простой разбор по модулям,
   - по умолчанию создаёт worktree для каждого задействованного модуля,
   - запускает wizard‑планирование (с вариантами A/B/C),
   - после Plan Gate запускает автономное исполнение (код/тесты/ревью без пользователя),
   - говорит “READY” **только когда гейты прошли**,
   - собирает ретро и улучшает workflow (через кастомизацию), не ломая core.

**Главные UX‑принципы:**
- Модуль — главная единица долгой памяти и контекста.
- По умолчанию worktree per module (opt‑out).
- Пользователь не должен помнить “много команд”; всё через `$csk`.
- Любая проблема → incident → обязательно в ретро.
- Апдейты workflow не ломают кастомизацию: **core заменяем, local overlay сохраняем**.

---

## 2) Ключевые проблемы текущего подхода (которые MUST решить редизайн)

### 2.1 Слишком “платформенно”
Смешивание в одном ядре:
- runtime оркестрации задач,
- инициатив/милстоунов,
- апдейта+миграции,
- overlay‑evolution + drift‑guard,
приводит к перегрузу UX и к хрупкости расширений.

### 2.2 Update/overlay сложнее, чем нужно
Механика “overlay drift guard + patchset allowlist + migration wizard” хороша концептуально, но слишком тяжела для solо UX и повышает вероятность “сломали себе процесс”.

### 2.3 Scope/verify логика должна быть worktree‑first
Если scope‑check смотрит “все изменения в репо”, а не изменения конкретного worktree/модуля/слайса — появляются ложные блокировки и ухудшение UX.

---

## 3) Архитектура CSK‑Next (строго 3 слоя)

### 3.1 Engine (ядро, vendor)
**Назначение:** минимальный набор операций, который обеспечивает enforce‑фазы.  
**Правило:** engine не кастомизируется правками. Только обновляется заменой.

### 3.2 Project State (долгоживущие данные проекта)
**Назначение:** память и статус, которые должны переживать чаты и годы.

### 3.3 Local Overlay (кастомизация)
**Назначение:** профили/плагины/настройки/skills overrides.  
**Правило:** апдейт engine НЕ трогает overlay.

---

## 4) Директории и артефакты (предлагаемый layout)

```
.csk/
  engine/                # vendor core (обновляемое)
    VERSION
    schemas/
    templates/
    skills_src/
    python/
  local/                 # кастомизация проекта (не трогается update)
    config.json
    profiles/
    skills_override/
    mcp_recommendations.json
    hooks/               # опционально
  app/                   # project state (durable)
    registry.json
    missions/
    logs/
    backlog.jsonl
    research/

.agents/skills/          # GENERATED from engine + local
AGENTS.md                # root + module AGENTS.md
tools/csk.py             # thin launcher (вызов engine cli)
```

### 4.1 “Generated skills”
**Важно:** `.agents/skills/` должен генерироваться из:
- `.csk/engine/skills_src/`
- `.csk/local/skills_override/`

Иначе апдейт будет вечно ломать руками правленные SKILL.md.

---

## 5) Сущности (термины)

- **Project**: весь репозиторий.
- **Module**: крупнейшая единица владения и памяти. Имеет свой kernel.
- **Mission**: большой запрос, который может затрагивать много модулей.
- **Milestone**: кусок миссии, который планируется и исполняется как “итерация”.
- **Task**: работа внутри модуля (единица “мы что-то делаем”).
- **Slice**: атомарный фрагмент задачи, исполняемый автономно одним агентом.
- **Proof Pack**: набор доказательств прохождения гейтов (scope/verify/review/e2e/user-check).
- **Decision log**: журнал решений (app-level и module-level).
- **Incident log**: журнал любых проблем/девиаций (app-level и module-level).

---

## 6) Enforce‑модель (что именно блокирует переходы)

### 6.1 Главные гейты
- **Plan Gate**: Plan Draft → Critic Review → Freeze → Plan Approval
- **Build Gate (slice)**: Scope‑check → Verify → Review → (E2E)
- **Ready Gate**: Validate‑Ready → Ready Approval
- **Retro Gate**: Retro обязателен на milestone/task closure

### 6.2 Доказательства (proofs)
По умолчанию proofs должны быть **worktree‑локальными** (чтобы не конфликтовать в git), но состояние “готовности” (READY status) отражается в durable state.

Рекомендуемая модель:
- Durable: plans, slices.json, freeze, approvals, decisions, incidents.
- Runtime (worktree): proofs, logs tails, attempts.

---

## 7) ФАЗЫ: детально

Ниже каждая фаза описана так, чтобы dev team мог реализовать её как state machine + CLI + skills.

---

# Phase 0 — Bootstrap / Adopt (подключение workflow)

## 0.1 Цели
- Сгенерировать минимальную структуру `.csk/` и `AGENTS.md`.
- Сформировать registry модулей (автодетект + подтверждение пользователем).
- Создать базовые module kernels только для нужных модулей (lazy adoption).

## 0.2 Входы
- Репозиторий новый (empty) **или** большой существующий.

## 0.3 Выходы (артефакты)
- `.csk/engine/` (если установлен pack)
- `.csk/local/` (пустой, но есть)
- `.csk/app/registry.json`
- `.agents/skills/` (generated)
- Root `AGENTS.md`
- В модуле: `AGENTS.md`, `.csk/module/` kernel skeleton, `PUBLIC_API.md`

## 0.4 UX (как выглядит)
Пользователь в root пишет: `$csk bootstrap`.

Ассистент:
- авто‑детектит модули (apps/, services/, packages/…);
- предлагает 2–3 варианта модульной карты и **рекомендацию**;
- создаёт kernels **только** для выбранных модулей (а не для всего репо).

## 0.5 Ошибки и обработка
- Если репо огромный и детект даёт 100+ модулей:
  - предложить режим “Pilot modules”: выбрать 1–3 модуля, остальные позже.
- Если структура нестандартная:
  - предложить Root‑as‑module (1 модуль = “.”) как временный режим.

## 0.6 Dev team implementation notes
- bootstrap должен быть idempotent.
- модульный детект — evidence-based (markers), не “спросить пользователя”.
- генерация skills должна быть стабильной и воспроизводимой.

---

# Phase 1 — Intake (root): принятие задачи/спеки

## 1.1 Цели
- Понять: задача маленькая (1 модуль) или большая (multi‑module).
- Сформировать понятное пользователю описание того, что будет сделано.
- Не лезть в детали модулей на root‑экране.

## 1.2 Входы
- Текст задачи/спеки/запроса от пользователя.

## 1.3 Выходы
- Классификация:
  - `single_module_task` | `multi_module_mission` | `unknown_need_discovery`
- Черновик routing (какие модули затронуты).
- Черновик milestone‑1 (если большая задача).

## 1.4 UX: “пользователь не технарь”
Интерфейс общения:
- предлагать варианты A/B/C (простыми словами),
- отмечать плюсы/минусы,
- явно показывать “что останется неизменным”.

## 1.5 Ошибки/неполнота
Если информации мало:
- root ассистент делает discovery:
  - быстро читает репо (high-level),
  - находит точки входа,
  - предлагает уточняющие вопросы (минимум), но всегда с вариантами ответов.

---

# Phase 2 — Routing + Worktrees (root): разложить по модулям и подготовить среду

## 2.1 Цели
- Определить модули для работы.
- Для каждого модуля:
  - создать worktree по умолчанию (opt‑out),
  - подготовить module context и public API sync.

## 2.2 Входы
- registry + задача.

## 2.3 Выходы
- Mission stub (если multi-module):
  - `.csk/app/missions/M-####/spec.md`
  - `.csk/app/missions/M-####/routing.json`
  - `.csk/app/missions/M-####/milestones.json` (минимум milestone-1)
- Module tasks stubs (на milestone‑1):
  - `<module>/.csk/tasks/T-####/plan.md`
  - `<module>/.csk/tasks/T-####/slices.json`
- Worktree mapping file:
  - `.csk/app/missions/M-####/worktrees.json` (module_id → worktree path)

## 2.4 Worktree policy
- Default: **worktree per module**.
- Opt‑out: пользователь явно говорит “no worktree”.

## 2.5 Ошибки/edge cases
- Если модуль не имеет отдельного build/test окружения:
  - root ассистент фиксирует как risk,
  - предлагает профили/пакеты улучшений позже (не блокирует planning).

---

# Phase 3 — Root Plan (Mission/Milestone planning)

## 3.1 Цели
- Сформировать “каркас” для milestone‑1:
  - что делает каждый модуль (на уровне целей),
  - какие есть зависимости между модулями (API change → consumers),
  - что можно параллелить, что sequential.

## 3.2 Выходы
- `milestones.json` с:
  - module_items,
  - depends_on,
  - parallelizable groups,
  - integration checks (если есть).

## 3.3 Важное правило
Root план НЕ лезет в детали “как именно в модуле”. Это задача Module planning.

---

# Phase 4 — Module Planning Wizard (в модуле)

## 4.1 Цели
- С пользователем подготовить детальный план:
  - варианты архитектуры/библиотек/паттернов,
  - почему выбранный вариант лучше,
  - что в scope, что non-scope,
  - как проверяем (гейты и тест-пирамида),
  - как режем на slices.

## 4.2 Входы
- root handoff: задача модуля + цель milestone‑1.

## 4.3 Выходы (артефакты)
- `plan.md` (человекочитаемый, максимально простой)
- `slices.json` (машиночитаемый: allowed_paths, required_gates, deps, traceability)
- `decisions.jsonl` (обязательные решения)
- optional: `research links` (если discovery делали)

## 4.4 “Не технарь” режим
Wizard обязан:
- предлагать варианты ответа (кнопки/варианты),
- давать рекомендованный вариант и причины,
- минимизировать свободный ввод пользователя.

---

# Phase 5 — Plan Gate (Critic → Freeze → Approval)

## 5.1 Цели
- Сделать план “достаточно хорошим” для автономного кодинга.
- Заблокировать кодинг до:
  - отсутствия P0/P1 в плане,
  - freeze,
  - approval.

## 5.2 Подфазы

### 5.2.1 Critic Review
- отдельный агент/роль, минимальный контекст (только план/слайсы/toolchain/public API)
- выдаёт P0/P1/P2/P3 и требуемые правки.

### 5.2.2 Freeze
- hashes plan + slices
- фиксирует “contract snapshot”.

### 5.2.3 Plan Approval (human)
- пользователь подтверждает “готово к работе”.
- approval пишется как артефакт.

## 5.3 Ошибки
- Drift после freeze → блок исполнения, требуется re‑critic → re‑freeze → re‑approve.

---

# Phase 6 — Execution Loop (slice-by-slice, автономно)

## 6.1 Цели
- Код пишется без пользователя.
- Каждый slice проходит строгий набор гейтов.
- Ретраи ограничены, чтобы не жечь токены.

## 6.2 Порядок для каждого slice
1) Implement (только в allowed_paths)
2) Scope‑check (must pass)
3) Verify (must pass required gates)
4) Review (must have p0=p1=0)
5) Optional E2E (if required)
6) Write proof pack artifacts
7) Update runtime status (progress)

## 6.3 Ограничение ретраев
- per slice: max_attempts = 2 (default)
- при превышении:
  - log incident (token_waste/stuck)
  - перевод задачи в “blocked” до решения пользователя (изменение план/профиля/окружения)

## 6.4 Ошибки и реакция
- Scope violation:
  - revert changes outside scope OR revise plan (re‑freeze)
- Verify fails:
  - log incident + remediation
  - если повторяется → retro candidate: environment/toolchain fix
- Review fails:
  - log incident + remediation (не тревожить пользователя)
- E2E missing but required:
  - blocked (нельзя READY)

---

# Phase 7 — READY Gate (Validate → Handoff → Human Approval)

## 7.1 Цели
- “READY” возможно только после machine validation.
- Пользователь получает короткий отчёт “что сделано + как проверить”.

## 7.2 Validate‑Ready must check
- freeze valid (no drift)
- plan approval exists
- latest scope proof ok
- verify coverage ok (all required gates executed & passed)
- review proof exists and p0/p1 == 0
- e2e proof ok if required
- user-check recorded (если вы сохраняете этот шаг)

## 7.3 Handoff report
- summary of changes
- proof references
- manual smoke steps (2–5 пунктов)

## 7.4 Human approval
- user records ready approval
- затем пользователь делает git операции.

---

# Phase 8 — Retro (обязательная)

## 8.1 Цели
- Любая проблема попадает в лог.
- После milestone/task — ретро обязательно.
- Ретро превращается в **конкретные улучшения**:
  - local overlay patches,
  - toolchain profile improvements,
  - предложенные MCP/skills.

## 8.2 Источники ретро
- incidents.jsonl (любые deviations)
- verify logs tails
- review findings
- user feedback

## 8.3 Результат ретро
- `retro.md` с:
  - clusters (env/toolchain/plan/test/process)
  - конкретные “patch proposals” (куда и что изменить)
- локальные изменения только в `.csk/local/` (не в engine)

---

# Phase 9 — Update / Upgrade workflow pack

## 9.1 Цели
- Обновить engine без потери кастомизации.
- Сохранить local overlay.

## 9.2 Механика
- Replace `.csk/engine/` целиком.
- Run:
  - `validate --all --strict`
  - regenerate `.agents/skills` from engine+local
- Wizard:
  - “что нового”
  - “что рекомендуется включить для этого проекта”
  - “что НЕ включаем (минимализм)”

## 9.3 Ошибки
- Если validate fails после update:
  - rollback engine version (simple: restore previous engine directory)
  - incident + retro

---

## 8) Профили и расширяемость (skills/MCP)

### 8.1 Profiles (data-driven)
`profiles/<stack>.json` должен определять:
- required gates
- default commands (если применимо)
- e2e requirements
- recommended linters/test frameworks
- recommended MCP/skills

### 8.2 MCP/Skills marketplace
Первая версия:
- workflow только **рекомендует** что поставить (links + rationale).
Вторая версия:
- skills можно устанавливать автоматически (copy into local overlay),
- MCP — пользователем (безопасность/доступы).

---

## 9) Сценарии (acceptance) — что dev team должен уметь пройти

### A) Greenfield
- init → single module → plan gate → 2 slices → ready → retro.

### B) Brownfield huge repo
- bootstrap pilot modules (1–3) → mission milestone‑1 → 2 modules in parallel → ready → retro.

### C) Cross-module API change
- owner module API slice → consumer slice → integration validation.

### D) Failures
- command not found → incident → doctor fix → rerun gate.
- scope violation → blocked until plan revision.
- repeated verify fail → stop retries → require human decision.

### E) Update
- update engine → local overlay preserved → skills regenerated → validate passes.

---

## 10) Implementation guidelines (clean code / OSS quality)

**Hard requirements:**
- No giant scripts. Prefer packages with small modules.
- Each file ≤ 200–300 LOC (except CLI wiring).
- Type hints everywhere.
- No silent fallbacks; all deviations -> incident.
- Deterministic execution (no shell pipelines in commands; use argv arrays).
- Idempotent operations (bootstrap, module init, api sync).

**Suggested internal structure:**
- `domain/` (models: Registry, Mission, Task, Slice, Proof, Incident)
- `io/` (atomic write, jsonl, path utils)
- `gates/` (scope, verify, review record, ready validate)
- `cli/` (argparse)
- `skills/` (template rendering and generation)
- `profiles/` (merge, overrides)

---

## 11) Decision points (что выбрать в дизайне)

Dev team должен принять несколько решений и зафиксировать их как ADR:

1) Proofs: хранить коммитом или в run/ (рекомендовано run/ worktree-local).
2) User-check обязателен или optional.
3) Default module mapping: strict per directory vs root-as-module fallback.
4) How to persist “module worktree path” mapping (в mission/worktree map).

---

## 12) Минимальный набор CLI API (внутренний, но стабильный)

Девелоперу нужно реализовать CLI команды (псевдо):

- `csk bootstrap`
- `csk module detect|add|init`
- `csk mission new|status|spawn-milestone`
- `csk task new|freeze|approve-plan|status`
- `csk slice run|mark`
- `csk gate scope-check|verify|record-review|validate-ready|approve-ready`
- `csk incident add`
- `csk retro run`
- `csk validate --all --strict`
- `csk update engine`

Пользователь напрямую их почти не вызывает; это backend для skills.

---

## 13) Skill set (минимум)

Обязательные skills:

- `$csk` — single entrypoint router
- `$csk-module` — module wizard
- `$csk-planner` — options A/B/C and explanations
- `$csk-critic` — plan critic
- `$csk-coder` — execute slices
- `$csk-reviewer` — strict review
- `$csk-qa` — optional e2e driver (profile-based)
- `$csk-retro` — retro and patch proposals
- `$csk-update-wizard` — init/update recommendations

Правило: **skills генерируются** из engine+local overlay.

---

## 14) Итог

CSK‑Next должен быть:
- удобным “solo” продуктом,
- worktree-first,
- module-first,
- с жёсткими гейтами, которые реально enforced,
- с расширяемостью через local overlay и профили,
- с update без перетирания кастомизаций.

Этот документ определяет фазы и артефакты. Код — задача dev team.

