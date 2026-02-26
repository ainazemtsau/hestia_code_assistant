# Phase-02 Sample Outputs

## 1) `./csk status --json` (strict user envelope)

```json
{
  "summary": {
    "project_phase": "PLANNING",
    "active_module_id": "root",
    "active_task_id": "T-0002",
    "bootstrapped": true
  },
  "status": "ok",
  "next": {
    "recommended": "csk run"
  },
  "refs": [
    "/home/anton/projects/hestia_code_assistant/.csk/modules/tasks/T-0002/plan.md"
  ],
  "errors": [],
  "data": {
    "project_phase": "PLANNING",
    "modules": [
      {
        "module_id": "root",
        "phase": "PLANNING",
        "task_status": "draft"
      }
    ],
    "counters": {
      "tasks_by_status": {
        "draft": 2
      },
      "proof_packs_total": 0,
      "retro_total": 0
    }
  }
}
```

## 2) `./csk status` (TTY text mode)

```text
SUMMARY:
phase=PLANNING bootstrapped=True mission=None milestone=None modules=2 skills=ok tasks=2 proofs=0 retro=0

STATUS:
- root: phase=PLANNING task=T-0002 slice=S-0001 progress=0/1
- m: phase=IDLE task=None slice=None progress=-

NEXT:
csk run
ALT: csk module root; csk status --json
```

## 3) `./csk module root` (TTY text mode)

```text
SUMMARY:
module=root path=.

STATUS:
phase=PLANNING task=T-0002 slice=S-0001 progress=0/1

NEXT:
csk run
ALT: csk module root; csk status --json
```
