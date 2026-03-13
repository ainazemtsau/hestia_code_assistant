# AGENTS.md — hestia_code_assistant workflow development repo

This repository is the development/factory repo for CSK-M Pro. It is not a client project with the workflow already installed.

Prime directives (hard)
- **Keep the product boundary explicit**: source repo, installable base, and client-owned customization layer must stay separate.
- **Do not treat repo-root files here as the exact files that will appear in client projects** unless they are intentionally placed in the installable asset set.
- **Thin bootstrap only**: client `AGENTS.md` must stay small and point Codex to deeper guides/skills instead of embedding the whole workflow.
- **Scripts are helpers**: use scripts only when they materially simplify repetitive file placement or managed-block updates. Instructions remain primary.
- **No command guessing**: if a scripted helper is needed, add it deliberately and document it.

Maintenance rules
- Any change to install, init, adopt, update, or bootstrap behavior must update the related client-facing instructions and skills in the same change.
- Any change to managed-vs-project-owned boundaries must update the install manifest and ownership documentation.
- Do not design updates that overwrite project-owned customizations.

Where to look
- Factory/source architecture: `docs/INSTALLATION_ARCHITECTURE.md`
- Client installed shape: `docs/CLIENT_WORKFLOW_LAYOUT.md`
- Client bootstrap model: `docs/CLIENT_BOOTSTRAP_MODEL.md`
- Installable assets: `install/`

Safety
- Prefer conservative changes to client-facing behavior.
- Avoid destructive commands.
- Keep install/update helpers narrow and reviewable.
- For source-repo work, start from the factory docs and local source-repo skills in this checkout, not the installed-client entrypoint.
