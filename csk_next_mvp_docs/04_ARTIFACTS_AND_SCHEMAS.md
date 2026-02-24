# 04 — Artifacts & Schemas (MVP)

Цель: стандартизировать файлы так, чтобы:
- гейты могли валидировать их “железно”,
- ассистенты могли генерировать их одинаково,
- пользователь мог читать их как менеджер.

## 4.1 Идентификаторы
- Mission: `M-0001`
- Milestone: `MS-1`, `MS-2`, …
- Task: `T-0001`
- Slice: `S-01`, `S-02`, …

## 4.2 Mission files (`.csk/app/missions/M-####/`)
- `spec.md` — исходная постановка
- `routing.json` — какие модули и почему
- `milestones.json` — roadmap; milestone-1 детальный
- `worktrees.json` — module_id → worktree path

## 4.3 Module task files (`<module>/.csk/tasks/T-####/`)
- `plan.md` — человекочитаемый план (A/B/C варианты, scope, checks)
- `slices.json` — машиночитаемое разбиение
- `freeze.json` — hash plan+slices (contract snapshot)
- `approvals.json` — approvals план/ready (human checkpoints)
- `decisions.jsonl` — решения (ADR-lite)
- `incidents.jsonl` — проблемы/девиации
- `run/proofs/*` — proof packs по слайсам
- `run/logs/*` — stdout/stderr verify команд
- `run/context/*` — сохранённые context bundles (опционально)

## 4.4 Минимальные JSON схемы (MVP)
Схемы должны жить в `.csk/engine/schemas/`:
- `event.schema.json`
- `slices.schema.json`
- `freeze.schema.json`
- `approvals.schema.json`
- `proofpack.schema.json`
- `registry.schema.json`

В MVP допускается “валидация руками” через код без jsonschema‑движка, но формат должен быть стабилен.

Шаблоны артефактов: см. `templates/artifacts/`.

