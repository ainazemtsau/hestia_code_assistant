# 03 — Directory Layout (MVP contract)

## 3.1 Root layout

```
.csk/
  engine/                # “vendor” ядро (в MVP в репо, но как слой)
    VERSION
    schemas/
    templates/
    skills_src/
  local/                 # overlay (не перетирать)
    config.json
    profiles/
    skills_override/
  app/                   # project state (durable)
    registry.json
    eventlog.sqlite      # или events.jsonl (если без SQLite)
    missions/
    logs/
    backlog.jsonl
    research/
.agents/skills/          # GENERATED (не редактировать руками)
AGENTS.md                # root инструктаж для ассистентов
tools/csk.py             # thin launcher (optional)
```

## 3.2 Module layout (внутри модуля)

```
<module>/
  AGENTS.md              # module-specific instructions
  .csk/
    module.json          # module metadata
    tasks/
      T-0001/
        plan.md
        slices.json
        freeze.json
        approvals.json
        decisions.jsonl
        incidents.jsonl
        run/
          proofs/
          logs/
          context/
```

## 3.3 Generated skills
`.agents/skills/` генерируется из:
- `.csk/engine/skills_src/`
- `.csk/local/skills_override/`

В MVP достаточно:
- root skill `$csk` (router)
- `$csk-planner`
- `$csk-critic`
- `$csk-coder`
- `$csk-status`
- `$csk-retro`

См. `07_SKILLS_SPEC.md` и `templates/skills/`.

