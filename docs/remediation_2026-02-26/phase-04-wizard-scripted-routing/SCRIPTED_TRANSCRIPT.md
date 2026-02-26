# Phase 04 Scripted Wizard Transcript

Дата: 2026-02-26

## Flow A (single module, inline JSON)
```bash
./csk run --answers-json '{"answers":{"intake_request":"Implement small API change","module_mapping":"app:modules/app","execution_shape":"single","planning_option":"B","confirm_materialization":"yes"}}' --non-interactive
```

Ожидаемый результат:
- `status=ok`
- `data.wizard.session_status=completed`
- `data.wizard.result.kind=single_module_task`
- Созданы `.csk/app/wizards/W-####/{session.json,events.jsonl,result.json}`

## Flow B (multi module, file answers)
```bash
./csk run --answers @answers-multi.json --non-interactive
```

`answers-multi.json`:
```json
{
  "answers": {
    "intake_request": "Change owner API and adapt consumer",
    "module_mapping": [
      "owner:modules/owner",
      "consumer:modules/consumer"
    ],
    "execution_shape": "multi",
    "planning_option": "B",
    "confirm_materialization": "yes"
  }
}
```

Ожидаемый результат:
- `status=ok`
- `data.wizard.result.kind=multi_module_mission`
- `data.wizard.result.artifacts.milestone_id=MS-0001`
- Созданы `routing.json`, `milestones.json`, `worktrees.json` в `mission_path`
