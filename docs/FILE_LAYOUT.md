# CSK‑M Pro v2 — File layout

## App level: .csk-app/
- registry.json: module boundaries (id->path, public API path)
- initiatives/: app-level specs and routing into modules
  - I-xxx/initiative.md: narrative for humans
  - I-xxx/initiative.plan.json: machine-readable roadmap and milestones
  - I-xxx/initiative.summary.md: short durable overview for sharing
  - I-xxx/initiative.status.json: derived progress and totals
  - I-xxx/approvals/initiative-plan-approve.json: optional approval proof for plan phase
  - I-xxx/reports: auto-generated migration/iteration reports (durable)
- public_apis/: synced module PUBLIC_API.md copies
- logs/*.jsonl: decisions/incidents (durable, append-only)
- backlog.jsonl: deferred work pool (durable)
- sync/: state/version data for updater (`state.json`, `history.jsonl`, `decisions/`, `migrations/`)
- run/: runtime state (ignored)

## Module level: <module>/.csk/
- memory/: module knowledge base (durable)
- digest.md: compact resume for new chats (durable)
- toolchain.json: gate commands (durable)
- public_apis/: synced contracts of other modules (durable)
- tasks/T-####/
  - plan.md, plan.summary.md (durable), user_acceptance.md (durable), slices.json, plan.freeze.json (durable)
  - approvals/ (durable)
  - approvals/user-check.json (durable)
  - run/ (ignored): proofs, active slice, attempt counters
- logs/*.jsonl: decisions/incidents (durable)

## Runtime vs durable
- Proof packs are runtime by default (ignored) to avoid merge/worktree conflicts.
- If you want to keep proofs, remove the ignore rule and accept merge complexity.
