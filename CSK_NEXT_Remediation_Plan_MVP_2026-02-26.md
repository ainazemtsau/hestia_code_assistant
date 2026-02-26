# CSK‑Next — Remediation Plan (MVP hardening to North Star)

Prepared: 2026-02-26  
Scope: `hestia_code_assistant` / CSK‑Next engine v0.1.x  
Audience: dev team (agents + humans).  

---

## 0) Цель и критерий «это заработало»

### 0.1. North Star критерий
Система считается **работающей как workflow**, если мы можем **в одном репозитории** (greenfield и brownfield) пройти end‑to‑end контур:

1) **Одна точка входа**: `./csk` (или `csk`) всегда выводит `SUMMARY / STATUS / NEXT`.
2) `NEXT` **детерминированен** и **всегда copy‑paste**.
3) `csk run` в `IDLE` **не no-op**, а запускает **wizard (intake→routing→planning)**.
4) План проходит **Plan Gate**: critic → freeze → human approve.
5) Исполнение идёт автономно slice‑by‑slice и не может «проскочить» гейты случайно.
6) `READY` появляется **только** после machine validation и human approve.
7) `retro` обязателен и создаёт **конкретный patch proposal** в local overlay.
8) `replay --check` воспроизводимо подтверждает инварианты по артефактам.
9) `update engine` заменяет core и **не ломает overlay**.

### 0.2. MVP acceptance сценарии (must pass)
Используем acceptance из фазовой спецификации:
- **A (Greenfield):** init → single module → plan gate → 2 slices → ready → retro.
- **B (Brownfield huge repo, пилот):** bootstrap pilot modules (1–3) → mission milestone‑1 → 2 modules in parallel → ready → retro.
- **E (Update):** update engine → local overlay preserved → skills regenerated → validate passes.

Сценарии C/D можно оставить как stretch, но минимум должны быть **скелеты команд/инвариантов**, чтобы не сломать дизайн.

### 0.3. Непробиваемые требования (Non‑negotiables)
- **Hard gates:** нельзя оказаться в `executing` без `plan_approved`; нельзя оказаться в `ready_validated` без proof‑pack; нельзя закрыть без `retro_done`.
- **SSOT:** eventlog — единственный журнал выполнения; артефакты должны иметь ссылки/manifest.
- **Overlay immutable by updates:** апдейт core не трогает `.csk/local`.
- **Worktree‑first по умолчанию** (для multi‑module), но MVP допускает *минимальную* реализацию (см. Phase 8).

---

## 1) Текущее состояние и «видимые проблемы» (по наблюдениям)

### 1.1. Состояние сейчас (сводно)
- Платформа «операционна»: `status=ok`, `validate/replay/doctor` проходят.
- Но **нет фактов E2E эксплуатации**: `proof packs = 0`, `retro = 0`, `missions executed = 0`.
- Есть UX‑неясности в отчётах: семантика `csk run` в `IDLE`, `initialized=false` у root.

### 1.2. Главный системный риск
Система может быть «технически стабильно запускаемой», но не доказано, что:
- state machine реально enforced в edge cases,
- `NEXT` ведёт пользователя по правильным шагам,
- артефакты/ивенты согласованы и replay ловит деградации,
- multi‑module/worktree не ломает state.

**Ремедиация** должна быть ориентирована на: **E2E proof + regression harness**.

---

## 2) План работ — фазы (атомарные, с артефактами и acceptance)

Ниже каждая фаза — небольшой «закрываемый» кусок. После каждой фазы обязателен прогон:

```bash
./csk validate --all --strict --skills
./csk replay --check
./csk doctor run --git-boundary
```

и запись итога в event log (`command.completed`) + короткий changelog в `docs/`.

### Phase 0 — Freeze спецификаций и устранение расхождений (1 PR)

**Зачем:** сейчас есть риск «две истины»: фазовая спецификация и полное описание проекта расходятся в деталях (например, расположение module state / proofs). Это источник скрытых багов.

**Deliverables:**
1) `docs/CONTRACT.md` — *единственный* canonical контракт:
   - layout директорий,
   - жизненный цикл task,
   - перечень команд (user + backend),
   - перечень артефактов (paths + schemas),
   - политика worktrees и где лежат runtime proofs.
2) `docs/ADR/ADR-0001-module-state-location.md`:
   - **решение**: где живут `tasks/` и где живут `run/proofs/`.
   - для MVP рекомендуем: durable state всегда в **одном месте**, runtime proofs — в worktree‑local месте.
3) `docs/ADR/ADR-0002-worktree-policy.md`:
   - где физически создаются worktrees,
   - как csk определяет «root state» из worktree,
   - как избегаем конфликтов proof‑директорий.

**Критерии приёмки:**
- Любой разработчик/агент может, читая только `docs/CONTRACT.md`, понять: какие файлы где должны появиться после каждого шага.

**Implementation notes:**
- Считать, что `PROJECT_FULL_DESCRIPTION_RU.md` — текущий SoT по UX/сущностям/псевдокоду; фазовую спецификацию привести к нему или явно пометить отличия.

---

### Phase 1 — Golden Path Acceptance A: полностью детерминированный E2E прогон в тестах

**Зачем:** без автоматического acceptance теста вы будете «чинить» наугад и ловить регрессии поздно.

**Deliverables:**
1) `engine/python/tests/test_acceptance_a_greenfield.py` (или расширение существующего `test_acceptance.py`):
   - создаёт временный репозиторий‑fixture,
   - выполняет команды (см. ниже) **неинтерактивно**,
   - проверяет артефакты на FS,
   - проверяет события в `eventlog.sqlite`,
   - прогоняет `replay --check`.
2) `docs/acceptance/A_GREENFIELD_TRANSCRIPT.md` — «золотая» CLI транскрипция (ожидаемые команды + ожидаемые ключевые строки SUMMARY/STATUS/NEXT).
3) `docs/acceptance/A_EXPECTED_ARTIFACTS.md` — список файлов, который обязан появиться.

**Ключевой дизайн‑требование для теста:**
- Нужен **scripted wizard** или backend API, чтобы test не зависел от TTY.

**Командный сценарий (минимальный):**
1) `./csk bootstrap` (или implicit bootstrap через `./csk`)
2) `./csk module add --module-id root --path .` *(если autodetect не создаёт root)*
3) `./csk module init --module-id root --write-scaffold`
4) `./csk new "MVP acceptance task" --module-id root --profile default`  
   - создаёт `Task` + 2 slices.
5) `./csk task critic --module-id root --task-id T-0001`
6) `./csk task freeze --module-id root --task-id T-0001`
7) `./csk task approve-plan --module-id root --task-id T-0001 --by "user"`
8) `./csk slice run --module-id root --task-id T-0001 --slice-id S-0001`
9) `./csk slice run --module-id root --task-id T-0001 --slice-id S-0002`
10) `./csk gate validate-ready --module-id root --task-id T-0001`
11) `./csk approve --ready --module-id root --task-id T-0001 --by "user"`
12) `./csk retro run --module-id root --task-id T-0001`
13) (опционально) `./csk task close --module-id root --task-id T-0001`

**Что должно быть в task fixture:**
- простая задача, которая реально меняет 1–2 файла и имеет простые verify команды (например, `python -m compileall` или `pytest -q`).

**Критерии приёмки:**
- Test проходит в CI стабильно.
- После `retro run` существует patch proposal в `.csk/local/patches/`.
- В `eventlog` есть события:
  - `task.created`, `slice.created` (2 шт.)
  - `task.critic_passed`
  - `task.frozen`
  - `task.plan_approved`
  - `proof.pack.written` (2 шт.)
  - `ready.validated`, `ready.approved`
  - `retro.completed`

---

### Phase 2 — STATUS/NEXT: единая модель состояния и «невозможность потеряться»

**Зачем:** в North Star UX пользователь не должен угадывать. `NEXT` — главный интерфейс.

**Deliverables:**
1) `csk status` выводит:
   - top‑level project phase,
   - список модулей (id/path/initialized/worktree if any),
   - active mission/task/slice (если есть),
   - counters: tasks in each status, proofs count, retro count.
2) `NEXT` строится **строго** по алгоритму роутинга (см. псевдокод в полном описании) и **всегда** относится к самому «горящему» блоку.
3) `--json` для всех user‑facing команд (`status`, `run`, `module`, `new`, `approve`, `retro`, `replay`) с одинаковой схемой:
   - `summary`, `status`, `next`, `refs` (пути к артефактам), `errors`.

**Implementation notes:**
- Реализовать `StatusModel` как read‑модель из FS + eventlog, но не «собирать в куче» в каждом handler.
- Нормализовать exit codes: `0 ok`, `10 validate fail`, `30 replay fail`, etc.

**Критерии приёмки:**
- После любой команды в stdout есть ровно один блок `NEXT:`.
- `csk` (без аргументов) == `csk status` (UX) и печатает такой же `NEXT`.

---

### Phase 3 — Module registry & init semantics: устранить путаницу `initialized=false`

**Зачем:** модуль — базовая единица долгой памяти. Семантика должна быть очевидна.

**Deliverables:**
1) Явное разделение:
   - `module registered` (есть запись в `.csk/app/registry.json`)
   - `module initialized` (есть kernel scaffold + AGENTS.md + публичные API файлы).
2) `csk module status --module-id X` выводит:
   - `registered=true/false`, `initialized=true/false`, `path`, `worktree_path (if any)`
   - `kernel_version` (если есть)
   - `NEXT` для этого модуля.
3) `csk module init --module-id X --write-scaffold`:
   - идемпотентен,
   - создаёт minimum scaffold,
   - пишет событие `module.initialized`.

**Критерии приёмки:**
- Acceptance A использует `module init` и больше не вызывает ambiguous состояния.

---

### Phase 4 — Wizard: scripted mode + routing output + materialization

**Зачем:** `csk run` должен быть удобным интейком (интерактивно), но тесты/CI/автоматизация требуют non‑interactive.

**Deliverables:**
1) Scripted wizard режим:
   - `csk run --answers @path/to/answers.json` или `--answers-json '{...}'`.
   - Wizard пишет артефакты: `session.json`, `events.jsonl`, `result.json`.
2) Wizard `module_mapping`:
   - MVP: явный mapping сохраняем, но добавляем **подсказки** (autodetect suggestions) без автопринятия.
3) Materialization:
   - создаётся `mission` (если multi‑module) и `tasks` (на milestone‑1) с `plan.md` и `slices.json`.

**Критерии приёмки:**
- Acceptance A может быть выполнен через `csk run --answers ...` (альтернатива прямым backend командам).
- Для IDLE состояние `NEXT=csk run` ведёт в wizard и создаёт task (не “ничего не сделал”).

---

### Phase 5 — Plan Gate hardening: critic → freeze → approve + drift enforcement

**Зачем:** это главный «человек‑в‑контуре» этап. Он должен быть простым и очень надёжным.

**Deliverables:**
1) `task critic`:
   - оценивает план по P0..P3,
   - запрещает переход дальше при P0/P1,
   - записывает `critic_report.json` (в task dir) и event `task.critic_passed` / `task.critic_failed`.
2) `task freeze`:
   - пишет `freeze.json` с hashes `plan.md` и `slices.json`,
   - event `task.frozen`.
3) `task approve-plan`:
   - пишет approval артефакт,
   - event `task.plan_approved`.
4) Drift enforcement:
   - любое изменение `plan.md`/`slices.json` после freeze → блокирует `slice run` до re‑critic/re‑freeze/re‑approve.

**Критерии приёмки:**
- Нельзя выполнить `slice run`, если:
  - task не `plan_approved`,
  - freeze отсутствует,
  - drift detected.

---

### Phase 6 — Slice execution loop: scope→verify→review→(e2e)→proof pack

**Зачем:** это автономный «движок работы». Он должен быть безопасным, воспроизводимым и строгим.

**Deliverables:**
1) `slice run` реализует цикл из полного описания:
   - snapshot before/after → changed_files
   - scope check по allowed_paths
   - verify runner (command policy: no pipes; denylist)
   - review record (p0/p1)
   - optional e2e
   - write proof pack + manifest
   - emit events `proof.pack.written`, `slice.completed`
2) `max_attempts` и `blocked`:
   - превышение попыток → incident + task.blocked.
3) Artifacts:
   - `proofs/<slice_id>/scope.json`
   - `proofs/<slice_id>/verify.json`
   - `proofs/<slice_id>/review.json`
   - `proofs/<slice_id>/e2e.json` (если применимо)
   - `proofs/<slice_id>/manifest.json`

**Критерии приёмки:**
- Acceptance A создаёт 2 proof packs.
- Scope violation приводит к failed slice и incident (и не даёт READY).

---

### Phase 7 — READY Gate: validate→handoff→approve

**Зачем:** «READY» — главный сигнал пользователю, его нельзя обесценить.

**Deliverables:**
1) `gate validate-ready`:
   - проверяет freeze/approval,
   - проверяет, что required proofs есть и passed,
   - проверяет verify coverage > 0,
   - генерирует `proofs/ready.json` + `proofs/READY/handoff.md`,
   - event `ready.validated`.
2) `approve --ready` (или `gate approve-ready`):
   - пишет approval,
   - event `ready.approved`.

**Критерии приёмки:**
- Acceptance A после 2 slices даёт validate-ready ok.
- handoff.md содержит:
  - список изменённых файлов,
  - команды verify, которые реально запускались,
  - минимальные smoke шаги.

---

### Phase 8 — Retro Gate: обязательная ретроспектива + patch proposals

**Зачем:** это механизм самоулучшения workflow через overlay.

**Deliverables:**
1) `retro run`:
   - разрешён только из `ready_approved` или `blocked`,
   - пишет `retro.md` (на основании incident log + gate failures + summary),
   - создаёт минимум 1 patch proposal в `.csk/local/patches/` (даже если “ничего не случилось” — пусть будет “no-op patch”).
   - event `retro.completed`.
2) `retro` меняет status task на `retro_done`.

**Критерии приёмки:**
- Acceptance A генерирует retro + patch.

---

### Phase 9 — Replay hardening: расширить инварианты до «невозможно скрытно сломать процесс»

**Зачем:** `replay --check` — ваш “black box flight recorder”. Сейчас проверок мало.

**Deliverables:**
1) Добавить инварианты (минимум):
   - все state transitions валидны (draft→...)
   - для `task.plan_approved` существует freeze + approval
   - для `slice.completed` существует `proof.pack.written` и manifest
   - для `ready.validated` существует ready.json + handoff.md
   - для `ready.approved` существует ready approval
   - для `retro.completed` существует retro.md + patch proposal
2) `replay --check` в выводе показывает:
   - список нарушений с путями к артефактам,
   - рекомендацию `NEXT` для исправления (например, `csk retro run ...`).

**Критерии приёмки:**
- Если вручную удалить `handoff.md`, replay должен падать.

---

### Phase 10 — Worktree per module (MVP): реализовать безопасный минимум

**Зачем:** это ключевая архитектура для больших задач, но MVP должен быть минимальным и не ломать single‑module.

**MVP‑решение (рекомендация):**
- Worktrees создаются только для multi‑module missions.
- Все команды пользователь вызывает в root; engine сам выполняет операции в worktree путях.

**Deliverables:**
1) `csk mission new` (или materialization из wizard) создаёт:
   - `.csk/app/missions/M-####/worktrees.json` (module_id → worktree path)
2) `csk module worktree create --module-id X --mission-id M-####`:
   - создаёт git worktree в `.csk/app/missions/M-####/worktrees/<module_id>/`.
3) Все file ops/commands в slice run должны иметь `workdir=worktree_path`.
4) Proofs должны быть worktree‑local либо mission‑scoped (чтобы 2 worktrees не перетирали друг друга).

**Acceptance B (pilot) минимальный:**
- 2 модуля, по 1 task в каждом, slices независимы.

---

### Phase 11 — Skills + UX для Codex: автодополнение и «одна точка входа»

**Зачем:** пользовательский UX — это не только engine, но и то, как ассистент видит команды.

**Deliverables:**
1) `./csk` wrapper всегда доступен и запускает engine.
2) Generated skills (`.agents/skills`) должны включать:
   - skill для `csk` (router)
   - skill‑обёртки для основных flows: `new`, `run`, `approve`, `module`, `retro`, `replay`, `update`.
3) В каждом skill:
   - перечислить точные команды (argv),
   - описать expected outputs,
   - указать «NEXT behaviour».
4) Док `docs/NEW_PROJECT_ONBOARDING.md` должен содержать «что вводить» и «как понять статус».

**Критерии приёмки:**
- Агенту достаточно “вызвать skill csk” и следовать NEXT, чтобы пройти Acceptance A.

---

### Phase 12 — Update engine (rollback-safe) + отчётность (manager report v2)

**Deliverables:**
1) `csk update engine`:
   - backup `.csk/engine`
   - replace engine
   - regenerate skills
   - strict validate
   - rollback on error + incident.
2) Manager report v2 (`csk report manager`):
   - counters: missions/tasks/slices/proofs/retro
   - last 20 non-ok events
   - ссылки на 3–5 CLI транскриптов
   - Engine/Overlay versions & drift status.

**Acceptance E:**
- update проходит, overlay не трогается, validate ok.

---

## 3) Приоритизация (что делать в каком порядке)

**P0 (нельзя дальше без этого):**
- Phase 0 (spec freeze)
- Phase 1 (Acceptance A test harness)
- Phase 2 (STATUS/NEXT deterministic)
- Phase 5–8 (гейты + proof/retro E2E)

**P1 (нужно для больших задач):**
- Phase 10 (worktrees minimal)
- Phase 4 (wizard scripted + routing)

**P2 (операционная зрелость):**
- Phase 9 (replay hardening)
- Phase 12 (update + report v2)

---

## 4) Командные «скрипты проверки» (готовые runbooks)

### 4.1. Smoke: чистый прогон Acceptance A вручную

```bash
./csk
# ожидаем: SUMMARY/STATUS/NEXT=csk run (или bootstrap)

./csk bootstrap
./csk module init --module-id root --write-scaffold

./csk run --answers @docs/acceptance/A_answers.json
# ожидаем: task создан, NEXT указывает на critic/freeze/approve

./csk run
# ожидаем: critic / freeze / approve / slice run ... (по NEXT)

./csk run
# повторять пока не получим READY

./csk retro run --module-id root --task-id T-0001
./csk replay --check
```

### 4.2. CI обязательные гейты (как в doc)

```bash
./csk validate --all --strict --skills
./csk replay --check
./csk doctor run --git-boundary
pytest -q
```

---

## 5) Риски и как их закрываем

1) **Несовместимость worktrees и .csk state** → решаем ADR + mission‑scoped proofs.
2) **Wizard зависит от TTY** → scripted answers обязательны.
3) **Gates можно обойти** (например, прямым редактированием файлов) → enforcement через state machine + replay invariants.
4) **Drift после freeze** → блок исполнения + понятный NEXT “re-freeze”.
5) **Слишком много команд** → user-facing поверхность фиксируем (6–7 команд), остальное backend.

---

## 6) Definition of Done (MVP)

MVP считается завершённым, когда:
- Acceptance A/B/E проходят в CI.
- `./csk` в любом состоянии выводит понятный `NEXT`.
- Есть хотя бы 1 реальный `proof pack` и 1 `retro` на настоящей задаче.
- Update core не ломает local overlay.

