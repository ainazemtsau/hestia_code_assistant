# Phase 1 Test Matrix

## Purpose

This matrix defines the minimum verification set for the Phase 1 clean rewrite.

Every row below must be green before cutover.

## Rules

- each scenario needs one automated test unless marked `manual`
- every automated test must fail before implementation and pass after implementation
- manual checks are required in addition to automated coverage, not instead of it
- no scenario may rely on the old live Phase 1 layer

## Matrix

### Install

`P1-INSTALL-001`
- Area: fresh install
- Setup: project contains a local workflow checkout and existing `AGENTS.md` in the parent project
- Action: run client install against shadow subsystem
- Expect:
  - managed base copied
  - starter `.csk-local/` created
  - managed bootstrap block inserted
  - installed skills listed in `AGENTS.md`

`P1-INSTALL-002`
- Area: existing project install
- Setup: parent project already contains unrelated files and client notes in `AGENTS.md`
- Action: run client install
- Expect:
  - unrelated files remain untouched
  - client notes remain
  - one managed block exists

`P1-INSTALL-003`
- Area: rerun install
- Setup: parent project already has installed workflow and edited `AGENTS.md` outside managed block
- Action: run client install again
- Expect:
  - managed files refresh
  - no duplicate managed block
  - client-owned content remains intact

`P1-INSTALL-004`
- Area: manifest path guard
- Setup: install manifest contains absolute path or escape path
- Action: run client install
- Expect:
  - operation fails before mutation

`P1-INSTALL-005`
- Area: CLI install
- Setup: realistic workflow checkout inside parent project
- Action: run `python tools/install_client_workflow.py`
- Expect:
  - install succeeds with default workflow root and default manifest
  - parent project receives managed base

## Update

`P1-UPDATE-001`
- Area: managed refresh
- Setup: installed client repo with stale managed file content
- Action: run client update
- Expect:
  - managed files match source base after update

`P1-UPDATE-002`
- Area: preserve project-owned customizations
- Setup: installed client repo with modified `.csk-local/README.md`
- Action: run client update
- Expect:
  - project-owned content unchanged

`P1-UPDATE-003`
- Area: stale managed asset removal
- Setup: client repo contains old managed asset no longer present in current manifest
- Action: run client update
- Expect:
  - stale managed asset removed

`P1-UPDATE-004`
- Area: legacy install without state file
- Setup: client repo has old managed asset and no hidden tracking file
- Action: run client update
- Expect:
  - stale managed asset still removed

`P1-UPDATE-005`
- Area: shape change file to directory
- Setup: target path exists as file, source now provides directory
- Action: run client update
- Expect:
  - old file removed
  - new directory copied cleanly

`P1-UPDATE-006`
- Area: shape change directory to file
- Setup: target path exists as directory, source now provides file
- Action: run client update
- Expect:
  - old directory removed
  - new file copied cleanly

`P1-UPDATE-007`
- Area: empty project root update
- Setup: empty client root
- Action: run client update directly
- Expect:
  - managed base installed
  - starter project-owned files created
  - bootstrap inserted

`P1-UPDATE-008`
- Area: stale bridge block removal
- Setup: client `AGENTS.md` contains local content plus managed bootstrap block, current manifest declares bridge cleanup target but no bridge asset
- Action: run client update
- Expect:
  - managed bootstrap block removed
  - local client content remains

`P1-UPDATE-009`
- Area: CLI update
- Setup: realistic workflow checkout inside parent project with installed workflow already present
- Action: run `python tools/update_client_workflow.py`
- Expect:
  - update succeeds with default workflow root and default manifest
  - managed files refresh
  - project-owned files remain intact

## Bootstrap

`P1-BOOTSTRAP-001`
- Area: installed skill discoverability
- Setup: fresh client install
- Action: inspect client `AGENTS.md`
- Expect:
  - `csk-init` is listed
  - `csk-adopt` is listed
  - `csk-project-update` is listed
  - each skill path is present

`P1-BOOTSTRAP-002`
- Area: thin bootstrap
- Setup: fresh client install
- Action: inspect client `AGENTS.md`
- Expect:
  - points to `.csk-base/ENTRYPOINT.md`
  - does not embed long guides or full workflow doctrine

`P1-BOOTSTRAP-003`
- Area: managed block update
- Setup: existing client `AGENTS.md` with local content plus managed block
- Action: rerun install or update
- Expect:
  - only managed block changes
  - local content outside block remains

## Manual E2E

`P1-MANUAL-001`
- Type: manual
- Area: install -> customize -> update
- Setup: local client fixture repo
- Action:
  - install
  - edit `.csk-local/README.md`
  - change managed source content
  - update
- Expect:
  - managed content refreshed
  - project-owned edit preserved
  - stale managed asset removed if applicable

`P1-MANUAL-002`
- Type: manual
- Area: CLI rerun in realistic local workflow checkout
- Setup: local parent project with embedded workflow checkout
- Action: run install/update through CLI scripts
- Expect:
  - default path resolution works
  - parent project is targeted
  - no git/network behavior is involved

## Cutover Gate

Cutover may start only when:
- all automated scenarios above are green
- all manual scenarios above are green
- helper-layer docs match actual behavior
