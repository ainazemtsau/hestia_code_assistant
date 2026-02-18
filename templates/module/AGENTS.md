# AGENTS.md (Module) — CSK‑M Pro v2

Scope constraint (hard)
- Only read/edit files under this module root.
- Cross-module knowledge is ONLY allowed via:
  - `.csk/public_apis/*` (synced contracts)
  - `PUBLIC_API.md` of this module
- Do not inspect other modules' source code.

Gates (hard)
- Plan Freeze + Plan Approval required for non-trivial tasks.
- Scope-check required (changes must be inside allowed paths).
- Verify gates must pass.
- Strict review must be recorded (review proof).
- Manual user acceptance must be recorded (`record-user-check`) before READY.
- If toolchain marks E2E required, E2E must pass.

Incident logging (mandatory)
Log an incident for ANY deviation:
- test failures, review findings P0/P1,
- plan gaps or ambiguity,
- environment/tool failures,
- token-waste loops (retries, command guessing),
- human rejects.
Write to: `.csk/logs/incidents.jsonl`
