# CSK‑M Pro v4 — Formal contracts

This folder provides JSON schema files under `/schemas`.
A developer can validate the contracts with any JSON Schema validator.

Built-in wrapper
- Use `python tools/csk/csk.py validate` to validate registry/toolchains/tasks/logs.
- If the optional `jsonschema` Python package is installed, the validator will also validate against the JSON Schema files under `/schemas`.

Contracts (files)
- `.csk-app/registry.json` -> `schemas/registry.schema.json`
- `<module>/.csk/toolchain.json` -> `schemas/toolchain.schema.json`
- `<module>/.csk/tasks/<task>/slices.json` -> `schemas/slices.schema.json`
- `<module>/.csk/tasks/<task>/plan.freeze.json` -> `schemas/plan_freeze.schema.json`
- runtime proofs under `run/proofs/`:
  - verify -> `schemas/verify_proof.schema.json`
  - scope -> `schemas/scope_proof.schema.json`
  - review -> `schemas/review_proof.schema.json`
  - e2e -> `schemas/e2e_proof.schema.json` (optional)

Log formats (append-only)
- incidents.jsonl -> `schemas/incident.schema.json`
- decisions.jsonl -> `schemas/decision.schema.json`
- backlog.jsonl -> `schemas/backlog_entry.schema.json`

Rule: tools must write data that validates against schemas.
