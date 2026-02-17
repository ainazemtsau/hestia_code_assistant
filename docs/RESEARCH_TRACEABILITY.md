# Research + traceability (CSK‑M Pro v2)

Goal: allow research to be done now and executed later without losing context.

Where research lives
- App-level: `.csk-app/research/`
- Module-level: `<module>/.csk/research/`

Format (recommended)
- `R-YYYYMMDD-<slug>.md`
  - Findings
  - Evidence/links
  - Candidate backlog items

Traceability
- Backlog entries link to research note path.
- Task plans include `Traceability` section with research ids/paths.
- Slice entries include `trace.research` so each slice can cite its research origin.

Tools
- `python tools/csk/csk.py research-new ...` creates a research note stub.
- `python tools/csk/csk.py backlog-add ...` records deferred tasks.
