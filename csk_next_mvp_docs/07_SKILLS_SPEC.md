# 07 — Skills Spec (MVP)

## 7.1 Зачем skills в MVP
1) UX “одна точка входа”: ассистенту проще следовать процедурам.
2) Автодополнение/Discoverability: ассистент видит список skills и может выбирать.
3) Отделение Engine от кастомизации: engine генерирует базовые skills, overlay может дополнять.

## 7.2 Правило генерации
`.agents/skills/` — **GENERATED**:
- source: `.csk/engine/skills_src/`
- overrides/additions: `.csk/local/skills_override/`

Внутри generated skills нельзя руками править.

## 7.3 Минимальный набор skills (MVP)
- `$csk` — root router (status/new/run/approve/module/retro)
- `$csk-planner` — wizard планирования (A/B/C)
- `$csk-critic` — critic plan gate
- `$csk-coder` — slice execution loop
- `$csk-status` — dashboard formatter
- `$csk-retro` — retro wizard (incidents → proposals)

## 7.4 Стандартный формат каждого skill
Каждый skill должен содержать:
- Purpose
- Inputs
- Steps (deterministic)
- Output format (включая `NEXT:`)
- Failure handling (как логировать incident)

Шаблоны: см. `templates/skills/`.

