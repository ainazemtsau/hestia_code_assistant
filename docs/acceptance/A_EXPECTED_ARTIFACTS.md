# Acceptance A Expected Artifacts

Файлы ниже обязательны после успешного completion сценария `A_GREENFIELD_TRANSCRIPT.md`.

| Path | Producer step | Assertion |
| --- | --- | --- |
| `.csk/app/eventlog.sqlite` | `csk bootstrap` + all commands | SQLite event log существует и содержит required event set. |
| `.csk/modules/tasks/T-0001/task.json` | `csk task new` | `status=retro_done` в финале. |
| `.csk/modules/tasks/T-0001/plan.md` | `csk task new` | План зафиксирован до freeze. |
| `.csk/modules/tasks/T-0001/slices.json` | fixture update | Содержит `S-0001` и `S-0002` с корректными deps. |
| `.csk/modules/tasks/T-0001/critic_report.json` | `csk task critic` | `p0=0`, `p1=0`, `passed=true`. |
| `.csk/modules/tasks/T-0001/freeze.json` | `csk task freeze` | Имеет plan/slices hashes. |
| `.csk/modules/tasks/T-0001/approvals/plan.json` | `csk task approve-plan` | Plan approval записан. |
| `.csk/modules/tasks/T-0001/approvals/ready.json` | `csk gate approve-ready` | READY approval записан. |
| `.csk/modules/tasks/T-0001/retro.md` | `csk retro run` | Retro документ создан. |
| `.csk/modules/run/tasks/T-0001/proofs/S-0001/scope.json` | `csk slice run ... S-0001` | Scope proof passed. |
| `.csk/modules/run/tasks/T-0001/proofs/S-0001/verify.json` | `csk slice run ... S-0001` | Verify proof passed, `executed_count > 0`. |
| `.csk/modules/run/tasks/T-0001/proofs/S-0001/review.json` | `csk slice run ... S-0001` | Review proof passed (`p0=0`, `p1=0`). |
| `.csk/modules/run/tasks/T-0001/proofs/S-0001/manifest.json` | `csk slice run ... S-0001` | Manifest существует для replay. |
| `.csk/modules/run/tasks/T-0001/proofs/S-0002/scope.json` | `csk slice run ... S-0002` | Scope proof passed. |
| `.csk/modules/run/tasks/T-0001/proofs/S-0002/verify.json` | `csk slice run ... S-0002` | Verify proof passed, `executed_count > 0`. |
| `.csk/modules/run/tasks/T-0001/proofs/S-0002/review.json` | `csk slice run ... S-0002` | Review proof passed (`p0=0`, `p1=0`). |
| `.csk/modules/run/tasks/T-0001/proofs/S-0002/manifest.json` | `csk slice run ... S-0002` | Manifest существует для replay. |
| `.csk/modules/run/tasks/T-0001/proofs/ready.json` | `csk gate validate-ready` | READY proof `passed=true`. |
| `.csk/modules/run/tasks/T-0001/proofs/READY/handoff.md` | `csk gate validate-ready` | Handoff markdown создан. |
| `.csk/local/patches/*.md` | `csk retro run` | Есть как минимум один patch proposal файл. |
