---
name: csk-project-update
description: Help a client project adapt after the managed CSK workflow base has been updated.
---

# `csk-project-update` — adapt after workflow update

Purpose
- Help the client understand and apply the impact of a managed workflow update.

Do
- Explain what changed in the managed workflow base.
- Check whether project-owned customizations may need adaptation.
- Recommend the next concrete workflow action.
- Point the client to `.csk-base/CHANGELOG.md`.
- Prefer adding project-specific follow-ups in `.csk-local/` instead of editing managed files.

Do not
- Overwrite project-owned customization files.
- Treat source-repo maintenance as the same thing as client-project update.

Primary guide
- `.csk-base/docs/UPDATE_GUIDE.md`
