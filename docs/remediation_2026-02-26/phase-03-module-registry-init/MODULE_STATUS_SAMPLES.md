# Phase 03 Module Status Samples

## Sample 1: registered + initialized module

Command:

```bash
./csk module status --module-id root --json
```

Key fields:

```json
{
  "status": "ok",
  "data": {
    "module": {
      "module_id": "root",
      "registered": true,
      "initialized": true,
      "path": ".",
      "worktree_path": null,
      "kernel_version": "1.0.0",
      "phase": "PLANNING"
    }
  }
}
```

## Sample 2: unregistered module

Command:

```bash
./csk module status --module-id ghost --json
```

Key fields:

```json
{
  "status": "ok",
  "data": {
    "module": {
      "module_id": "ghost",
      "registered": false,
      "initialized": false,
      "path": null,
      "worktree_path": null,
      "kernel_version": null,
      "phase": "UNREGISTERED"
    }
  },
  "next": {
    "recommended": "csk module add --path <repo-relative-path> --module-id ghost"
  }
}
```

## Sample 3: idempotent init + event

Command:

```bash
./csk module init --module-id root --write-scaffold
./csk event tail --n 20 --type module.initialized --module-id root
```

Observed payload:

```json
{
  "already_initialized": true,
  "kernel_created": false,
  "scaffold_created": [],
  "registered": true,
  "initialized": true
}
```

Observed event:

- `type`: `module.initialized`
- `id`: `1ab403a1-6564-4997-a7c8-1d9a465e8d27`
- `ts`: `2026-02-26T12:34:10Z`
