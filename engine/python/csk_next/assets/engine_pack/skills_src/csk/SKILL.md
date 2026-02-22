# $csk

Single entrypoint router for CSK-Next.

## Flow
1. Run `csk run` as the default interaction path.
2. Collect wizard answers step-by-step until artifacts are materialized.
3. Continue with phase gates via backend CLI commands.

## Guardrails
- Do not bypass wizard planning.
- Do not bypass phase gates.
- Record incidents for all deviations.
