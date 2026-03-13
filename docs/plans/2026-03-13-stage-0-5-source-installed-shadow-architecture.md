# Stage 0.5 — Source / Installed / Shadow Architecture

## Summary

`Stage 0.5` locks the repo boundary so there is one unambiguous redesign truth:

- `shadow/canonical/` is the only active redesign source
- `live` remains compatibility-only until final cutover
- `shadow/phase1-clean/` is legacy-reference-only and must not receive new work
- install/update/runtime behavior is not redesigned in this stage
- future cutover must replace from `shadow/canonical/`, never from memory and never from mixed live/shadow state

## Surface Classes

| Class | Meaning |
| --- | --- |
| `canonical-active` | The only active redesign source. New workflow design work lands here. |
| `live-compatibility` | Live repo surfaces that still exist and may remain usable, but are not redesign truth. |
| `legacy-reference` | Historical or failed intermediate surfaces kept only for reference until deletion. |
| `installed-client-surface` | Files whose purpose is to be installed into client projects; canonical content lives in `shadow/canonical/client-package/`, while live copies remain compatibility-only until cutover. |

## Hard Rules

- all new redesign work lands only in `shadow/canonical/`.
- `live` may receive only:
  - compatibility maintenance
  - status/doc alignment
  - explicit final cutover work
- `shadow/phase1-clean/` is not a design target anymore.
- No partial migration from `phase1-clean` is allowed.
- Future cutover replaces from `shadow/canonical/`, not from memory and not from mixed live/shadow state.
- No new public docs may describe `phase1-clean` as current or recommended.

## Exact Semantics By Surface Type

| Surface type | Current rule |
| --- | --- |
| Source repo surfaces | Live repo entrypoints, docs, and tests remain compatibility-only unless they already live under `shadow/canonical/`. |
| Installed client package surfaces | `install/` is the live compatibility copy; `shadow/canonical/client-package/install/` is the future source of truth. |
| Delivery-only surfaces | Live delivery helpers remain compatibility-only; `shadow/canonical/delivery/` is the only redesign target. |
| Cutover-only metadata | Cutover manifests and boundary maps live under `shadow/canonical/cutover/` and are canonical-active even before final cutover. |

## Canonical-Active Paths

| Path | Reason | Owner stage |
| --- | --- | --- |
| `shadow/canonical/runtime/` | Canonical home for runtime redesign work. | `Stage 1`–`Stage 6` |
| `shadow/canonical/client-package/` | Canonical home for installed client package design. | `Stage 7` |
| `shadow/canonical/delivery/` | Canonical home for thin install/update delivery. | `Stage 8` |
| `shadow/canonical/tests/` | Canonical home for redesign-stage acceptance tests. | `Stage 8` |
| `shadow/canonical/cutover/` | Canonical home for replace/delete policy and cutover metadata. | `Stage 9` |

## Live-Compatibility Paths

| Path | Reason | Owner stage |
| --- | --- | --- |
| `tools/csk/install_lib.py` | Live delivery helper remains usable, but future truth comes from canonical delivery. | `Stage 8` |
| `tools/csk/install_client_workflow.py` | Live install entrypoint remains compatibility-only until cutover. | `Stage 8` |
| `tools/csk/update_client_workflow.py` | Live update entrypoint remains compatibility-only until cutover. | `Stage 8` |
| `.csk-app/digest.md` | Active repo status surface; must reflect canonical-only redesign policy now. | `Stage 0.5` |
| `shadow/README.md` | Active workspace guidance; must clearly mark canonical vs legacy. | `Stage 0.5` |
| `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md` | Active redesign control-plane document. | `Stage 0.5` |
| `docs/plans/2026-03-13-stage-0-global-workflow-audit.md` | Active audit reference, but not redesign source. | `Stage 0.5` |
| `docs/plans/2026-03-13-stage-0-workflow-inventory.json` | Active audit inventory reference, but not redesign source. | `Stage 0.5` |
| `docs/plans/2026-03-13-stage-0-5-source-installed-shadow-architecture.md` | Active architecture reference for future stages. | `Stage 0.5` |

## Legacy-Reference Paths

| Path | Reason | Owner stage |
| --- | --- | --- |
| `shadow/phase1-clean/` | Previous rewrite attempt kept only for comparison until final deletion. | `Stage 9` |

## Installed-Client-Surface Paths

| Path | Reason | Owner stage |
| --- | --- | --- |
| `install/` | Live compatibility copy of the installed client package. | `Stage 7` |
| `shadow/canonical/client-package/install/` | Canonical source of truth for the installed client package. | `Stage 7` |

## Replace-at-Cutover Paths

| Live path | Canonical source | Reason |
| --- | --- | --- |
| `install/` | `shadow/canonical/client-package/install/` | Replace the whole live client-package tree from canonical package source. |
| `tools/csk/install_lib.py` | `shadow/canonical/delivery/tools/csk/install_lib.py` | Replace live delivery helper from canonical delivery source. |
| `tools/csk/install_client_workflow.py` | `shadow/canonical/delivery/tools/csk/install_client_workflow.py` | Replace live install CLI from canonical delivery source. |
| `tools/csk/update_client_workflow.py` | `shadow/canonical/delivery/tools/csk/update_client_workflow.py` | Replace live update CLI from canonical delivery source. |
| `tests/test_bootstrap_contract.py` | `shadow/canonical/tests/` | Future canonical tests must own the live compatibility gate. |
| `tests/test_client_install_flow.py` | `shadow/canonical/tests/` | Future canonical tests must own the live compatibility gate. |
| `tests/test_client_install_manifest.py` | `shadow/canonical/tests/` | Future canonical tests must own the live compatibility gate. |
| `tests/test_client_install_update_e2e.py` | `shadow/canonical/tests/` | Future canonical tests must own the live compatibility gate. |
| `tests/test_client_update_preserves_customizations.py` | `shadow/canonical/tests/` | Future canonical tests must own the live compatibility gate. |
| `tests/test_install_lib.py` | `shadow/canonical/tests/` | Future canonical tests must own the live compatibility gate. |
| `tests/test_source_repo_agents.py` | `shadow/canonical/tests/` | Future canonical tests must own the source/client boundary gate. |

## Delete-at-Cutover Paths

| Path | Reason |
| --- | --- |
| `shadow/phase1-clean/` | Legacy duplicate that must be removed rather than migrated. |

## Stage-Level Cutover Rules

- `Stage 1`–`Stage 8` may only implement against canonical targets.
- If a live compatibility surface needs behavior change before cutover, the canonical source must be updated first and the live change treated as compatibility maintenance only.
- No stage may treat `phase1-clean` as a migration source.
- `Stage 9` must cut over by exact path mapping from canonical replace/delete manifests, not by manual selection.

## Acceptance

- no ambiguity remains between source, installed, legacy, and canonical surfaces
- `shadow/canonical/` is the only active redesign workspace in active docs
- `shadow/phase1-clean/` is clearly marked legacy-reference-only
- exact replace/delete mapping exists on disk
- future stages can implement only in canonical and still know exactly how live will be replaced later
