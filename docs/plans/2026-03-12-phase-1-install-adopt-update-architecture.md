# Phase 1 Install Adopt Update Architecture Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
>
> **Status:** This document remains the architectural source for Phase 1 goals, but it is no longer the direct execution plan.
> Execute the clean rewrite track in `docs/plans/2026-03-13-phase-1-clean-rewrite.md` first.

**Goal:** Build the distribution architecture for CSK so the source repo can install a complete client-facing workflow into another project, preserve client customizations across updates, and keep development-only assets out of the installed workflow.

**Architecture:** Treat this repository as the workflow factory and package source, not as the installed client runtime. Introduce a curated installable base layer, a separate project-owned customization layer, and a thin client bootstrap that points Codex to deeper skills and guides. Install and update remain guided operations for Codex, with helper scripts only where they materially reduce repetitive file placement or managed-block edits.

**Tech Stack:** Markdown guides, Codex skills, Python stdlib helper scripts, JSON manifests, unittest-based repo tests.

### Task 1: Define the source-vs-installed architecture

**Files:**
- Modify: `README_CSKM_PRO.md`
- Modify: `AGENTS.md`
- Create: `docs/INSTALLATION_ARCHITECTURE.md`
- Create: `docs/CLIENT_WORKFLOW_LAYOUT.md`
- Create: `docs/CLIENT_BOOTSTRAP_MODEL.md`

**Step 1: Write the failing architecture review notes**

Create a short checklist in `docs/INSTALLATION_ARCHITECTURE.md` that fails the current model for these reasons:
- source repo is mixed with installed runtime
- installable assets are not explicitly defined
- client customization layer is missing
- client bootstrap is too ambiguous

Expected result: the document explicitly says the current repo shape is not yet a valid install model.

**Step 2: Rewrite the root README install story**

Update `README_CSKM_PRO.md` so it no longer says “copy all files into repo root.” Replace that with source-repo-as-factory language and a curated installable set.

**Step 3: Rewrite the dev AGENTS rule**

Update `AGENTS.md` so this repo is clearly the development repo for the workflow, not a client repo that already “uses CSK” in the same way an installed project would.

**Step 4: Document the installed client shape**

Write `docs/CLIENT_WORKFLOW_LAYOUT.md` with the three-layer model:
- base workflow layer
- project customization layer
- optional helper layer

**Step 5: Document the bootstrap model**

Write `docs/CLIENT_BOOTSTRAP_MODEL.md` to define the thin client `AGENTS.md`, what it must contain, and what must be kept out of it.

**Step 6: Commit**

```bash
git add README_CSKM_PRO.md AGENTS.md docs/INSTALLATION_ARCHITECTURE.md docs/CLIENT_WORKFLOW_LAYOUT.md docs/CLIENT_BOOTSTRAP_MODEL.md
git commit -m "docs: define source and installed workflow architecture"
```

### Task 2: Define the installable asset manifest and ownership rules

**Files:**
- Create: `install/manifest/client_base_manifest.json`
- Create: `install/manifest/ownership_rules.md`
- Create: `install/source/base/.csk-base/README.md`
- Create: `install/source/base/.csk-local/README.md`
- Create: `install/source/bridge/root_AGENTS_managed_block.md`
- Modify: `docs/INSTALLATION_ARCHITECTURE.md`
- Test: `tests/test_client_install_manifest.py`

**Step 1: Write the failing manifest test**

Create `tests/test_client_install_manifest.py` with checks for:
- manifest file exists
- every manifest entry has `source`, `target`, and `ownership`
- ownership is one of `managed`, `bridge`, `project-owned-template`
- manifest excludes dev-only files like repo root `AGENTS.md`, `.gitignore`, and `.codex/config.toml`

Example skeleton:

```python
import json
import unittest
from pathlib import Path


class ClientInstallManifestTests(unittest.TestCase):
    def test_manifest_has_required_fields(self):
        path = Path("install/manifest/client_base_manifest.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(data.get("assets"), list)
        self.assertTrue(data["assets"])


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_client_install_manifest -v
```

Expected: FAIL because manifest files do not exist yet.

**Step 3: Create the manifest and ownership docs**

Define:
- what is installed into client projects
- what is never installed
- what is inserted as a managed bridge block
- what is created as project-owned starter files

**Step 4: Create the install-source layout**

Seed:
- `install/source/base/.csk-base/README.md`
- `install/source/base/.csk-local/README.md`
- `install/source/bridge/root_AGENTS_managed_block.md`

These files should describe their future role, not final runtime behavior yet.

**Step 5: Run test to verify it passes**

Run:

```bash
python -m unittest tests.test_client_install_manifest -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add install/manifest/client_base_manifest.json install/manifest/ownership_rules.md install/source/base/.csk-base/README.md install/source/base/.csk-local/README.md install/source/bridge/root_AGENTS_managed_block.md tests/test_client_install_manifest.py docs/INSTALLATION_ARCHITECTURE.md
git commit -m "feat: define installable asset manifest"
```

### Task 3: Build the thin client bootstrap and managed AGENTS merge path

**Files:**
- Create: `install/source/base/.csk-base/ENTRYPOINT.md`
- Create: `install/source/base/.csk-base/docs/INIT_GUIDE.md`
- Create: `install/source/base/.csk-base/docs/UPDATE_GUIDE.md`
- Create: `install/source/base/.agents/skills/csk-init/SKILL.md`
- Create: `install/source/base/.agents/skills/csk-adopt/SKILL.md`
- Create: `install/source/base/.agents/skills/csk-project-update/SKILL.md`
- Create: `tools/csk/install_lib.py`
- Test: `tests/test_client_agents_merge.py`

**Step 1: Write the failing AGENTS merge test**

Create `tests/test_client_agents_merge.py` to verify:
- an existing client `AGENTS.md` keeps its own content
- the installer adds exactly one managed CSK block
- rerunning the merge updates only the managed block
- no full-file replacement occurs

**Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_client_agents_merge -v
```

Expected: FAIL because the merge helper does not exist yet.

**Step 3: Create the thin bootstrap assets**

Add:
- `ENTRYPOINT.md`
- `INIT_GUIDE.md`
- `UPDATE_GUIDE.md`
- init/adopt/update skills

The bootstrap must only explain:
- that the workflow is installed
- where the entrypoint is
- how to enter root mode
- where deeper guides live

**Step 4: Implement the managed-block helper**

In `tools/csk/install_lib.py`, add a focused helper that:
- creates `AGENTS.md` if missing
- inserts one managed block if file exists
- updates only that block on rerun

Do not implement a generic merge engine.

**Step 5: Run test to verify it passes**

Run:

```bash
python -m unittest tests.test_client_agents_merge -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add install/source/base/.csk-base/ENTRYPOINT.md install/source/base/.csk-base/docs/INIT_GUIDE.md install/source/base/.csk-base/docs/UPDATE_GUIDE.md install/source/base/.agents/skills/csk-init/SKILL.md install/source/base/.agents/skills/csk-adopt/SKILL.md install/source/base/.agents/skills/csk-project-update/SKILL.md tools/csk/install_lib.py tests/test_client_agents_merge.py
git commit -m "feat: add thin client bootstrap and managed AGENTS merge"
```

### Task 4: Implement the install helper for new and existing client projects

**Files:**
- Create: `tools/csk/install_client_workflow.py`
- Modify: `tools/csk/install_lib.py`
- Modify: `install/manifest/client_base_manifest.json`
- Create: `docs/CLIENT_INSTALL.md`
- Test: `tests/test_client_install_flow.py`

**Step 1: Write the failing install flow test**

Create `tests/test_client_install_flow.py` to verify:
- install copies all managed base assets from `install/source/base`
- install creates `.csk-base/` and starter `.csk-local/`
- install merges the bootstrap block into client `AGENTS.md`
- install does not copy repo dev files into the client project

**Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_client_install_flow -v
```

Expected: FAIL because install helper does not exist yet.

**Step 3: Implement the installer**

Add a narrow helper script that:
- takes a target project path
- reads the client base manifest
- copies managed assets
- creates starter customization files if missing
- applies the AGENTS managed block
- prints a human-readable summary

**Step 4: Document the install operation**

Write `docs/CLIENT_INSTALL.md` with:
- what install does
- what it does not do
- what Codex should do next with `csk-init` or `csk-adopt`

**Step 5: Run test to verify it passes**

Run:

```bash
python -m unittest tests.test_client_install_flow -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add tools/csk/install_client_workflow.py tools/csk/install_lib.py install/manifest/client_base_manifest.json docs/CLIENT_INSTALL.md tests/test_client_install_flow.py
git commit -m "feat: add client workflow installer"
```

### Task 5: Implement the update helper without overwriting project customizations

**Files:**
- Create: `tools/csk/update_client_workflow.py`
- Modify: `tools/csk/install_lib.py`
- Create: `install/source/base/.csk-base/CHANGELOG.md`
- Create: `docs/CLIENT_UPDATE.md`
- Test: `tests/test_client_update_preserves_customizations.py`

**Step 1: Write the failing update preservation test**

Create `tests/test_client_update_preserves_customizations.py` to verify:
- update refreshes managed base assets
- update refreshes the managed AGENTS block only
- update leaves `.csk-local/` untouched
- update reports changed files and references changelog guidance

**Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_client_update_preserves_customizations -v
```

Expected: FAIL because update helper does not exist yet.

**Step 3: Implement the updater**

Add a helper script that:
- reads the same manifest as install
- updates managed assets only
- does not overwrite `.csk-local/`
- updates only the managed AGENTS block
- prints a summary suitable for Codex to explain to the client

**Step 4: Add update guidance**

Write:
- `.csk-base/CHANGELOG.md` as the installed human-readable change surface
- `docs/CLIENT_UPDATE.md` for the source repo operator

**Step 5: Run test to verify it passes**

Run:

```bash
python -m unittest tests.test_client_update_preserves_customizations -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add tools/csk/update_client_workflow.py tools/csk/install_lib.py install/source/base/.csk-base/CHANGELOG.md docs/CLIENT_UPDATE.md tests/test_client_update_preserves_customizations.py
git commit -m "feat: add client workflow updater"
```

### Task 6: Wire init, adopt, and update guidance into the installed base

**Files:**
- Modify: `install/source/base/.csk-base/ENTRYPOINT.md`
- Modify: `install/source/base/.csk-base/docs/INIT_GUIDE.md`
- Modify: `install/source/base/.csk-base/docs/UPDATE_GUIDE.md`
- Modify: `install/source/base/.agents/skills/csk-init/SKILL.md`
- Modify: `install/source/base/.agents/skills/csk-adopt/SKILL.md`
- Modify: `install/source/base/.agents/skills/csk-project-update/SKILL.md`
- Create: `install/source/base/.csk-local/examples/review.browser.md`

**Step 1: Write the init/adopt/update operator stories**

In the installed guides, explain:
- fresh install into a new repo
- adopt into an existing repo
- update followed by Codex-assisted adaptation

**Step 2: Make Codex assistance explicit**

The skills must tell Codex to help the client:
- inspect project structure
- propose modules
- explain what changed after update
- suggest where project customizations may need adaptation

**Step 3: Seed one customization example**

Add `review.browser.md` as an example project-owned override so the boundary between base and customization is concrete.

**Step 4: Review for thinness**

Ensure `ENTRYPOINT.md` stays thin. Move anything long or detailed back into the deeper guides.

**Step 5: Commit**

```bash
git add install/source/base/.csk-base/ENTRYPOINT.md install/source/base/.csk-base/docs/INIT_GUIDE.md install/source/base/.csk-base/docs/UPDATE_GUIDE.md install/source/base/.agents/skills/csk-init/SKILL.md install/source/base/.agents/skills/csk-adopt/SKILL.md install/source/base/.agents/skills/csk-project-update/SKILL.md install/source/base/.csk-local/examples/review.browser.md
git commit -m "docs: add client init adopt and update guidance"
```

### Task 7: Separate repo-maintainer update paths from client update paths

**Files:**
- Modify: `.agents/skills/csk-update/SKILL.md`
- Modify: `docs/csk-upstream-update.md`
- Modify: `tools/csk/upstream_sync_manifest.json`
- Modify: `README_CSKM_PRO.md`
- Test: `tests/test_upstream_manifest_excludes_client_bridge_targets.py`

**Step 1: Write the failing upstream manifest test**

Create `tests/test_upstream_manifest_excludes_client_bridge_targets.py` to verify that source-repo upstream sync is not presented as the same operation as client project update.

**Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_upstream_manifest_excludes_client_bridge_targets -v
```

Expected: FAIL because the source update story is still mixed with client update assumptions.

**Step 3: Rewrite maintainer update guidance**

Clarify that:
- `csk-update` in this repo is for maintaining the workflow source/base
- `csk-project-update` in installed client repos is for helping clients adapt their installed workflow

**Step 4: Fix the source sync manifest**

Remove client-facing ambiguity from `tools/csk/upstream_sync_manifest.json`. The manifest should describe source repo asset sync, not client project update semantics.

**Step 5: Run test to verify it passes**

Run:

```bash
python -m unittest tests.test_upstream_manifest_excludes_client_bridge_targets -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add .agents/skills/csk-update/SKILL.md docs/csk-upstream-update.md tools/csk/upstream_sync_manifest.json README_CSKM_PRO.md tests/test_upstream_manifest_excludes_client_bridge_targets.py
git commit -m "docs: split maintainer update from client update"
```

### Task 8: Run the Phase 1 verification pass and update the roadmap

**Files:**
- Modify: `docs/plans/2026-03-09-best-workflow-overhaul.md`
- Modify: `.csk-app/digest.md`
- Modify: `docs/INSTALLATION_ARCHITECTURE.md`

**Step 1: Run all new tests**

Run:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Expected: PASS.

**Step 2: Run existing validation**

Run:

```bash
python tools/csk/csk.py validate --all --strict
```

Expected: PASS or only errors that are explicitly explained by the source-repo redesign and fixed before completion.

**Step 3: Update the older master roadmap**

Mark in `docs/plans/2026-03-09-best-workflow-overhaul.md` that install/adopt/update architecture is now a separate prerequisite track and that later phases depend on it.

**Step 4: Update the source repo digest**

Revise `.csk-app/digest.md` so the repo is no longer described as if it were already the installed client workflow.

**Step 5: Commit**

```bash
git add docs/plans/2026-03-09-best-workflow-overhaul.md .csk-app/digest.md docs/INSTALLATION_ARCHITECTURE.md
git commit -m "chore: close phase 1 install architecture loop"
```

## Batch Suggestions

- Batch 1:
  - Task 1
  - Task 2

- Batch 2:
  - Task 3
  - Task 4

- Batch 3:
  - Task 5
  - Task 6

- Batch 4:
  - Task 7
  - Task 8

## Hard Rules for Execution

- Do not reuse the old “copy the repo into client project” mental model.
- Keep base workflow assets and project-owned customizations separate from the first commit.
- Do not put full workflow knowledge into the client `AGENTS.md`.
- Do not add complex validators where Codex instructions are enough.
- Helper scripts must stay narrow and support Codex; they are not the center of the workflow.
- Any install/update behavior change must update the corresponding install/init/adopt/update instructions and skills in the same batch.

## Definition of Done

- Source repo and installed client workflow are clearly separated.
- Installable assets are explicit and test-covered.
- Client bootstrap is thin and managed-block based.
- Install creates a complete client-facing base workflow, not a partial shell.
- Update refreshes managed assets without overwriting project customizations.
- Client-facing init/adopt/update guidance exists inside the installed base.
- Repo-maintainer update flows are clearly separated from client update flows.
