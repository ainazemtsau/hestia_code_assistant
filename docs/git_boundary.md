# Git Boundary Policy

This repository should publish product code/docs only. Runtime state from CSK must stay outside product commits.

## Forbidden in product Git

- `.csk/**`
- `.agents/**`
- `AGENTS.md` (root)
- `**/.csk/**`
- `__pycache__/**`
- `*.pyc`

## Allowed in product Git

- `engine/python/**`
- `tools/**`
- `docs/**`
- `README.md`
- `pyproject.toml`
- product documentation such as `csk_next_mvp_docs/**` (if intentionally part of product docs)

## Pre-push checklist

1. `PYTHONPATH=engine/python python -m csk_next.cli.main --root . doctor run --git-boundary`
2. `git status --short`
3. `git diff --cached --name-only`

If boundary warnings appear, remove or unstage forbidden files before pushing.
