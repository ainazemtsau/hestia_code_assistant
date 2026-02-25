"""PKM v0 runbook extraction from verify events."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from csk_next.eventlog.store import append_event, query_events
from csk_next.io.files import ensure_dir, read_json, write_json
from csk_next.runtime.paths import Layout
from csk_next.runtime.time import utc_now_iso


def _pkm_path(layout: Layout) -> Path:
    return layout.app / "pkm" / "items.json"


def _load_items(layout: Layout) -> dict[str, Any]:
    path = _pkm_path(layout)
    if not path.exists():
        return {"schema_version": "1.0.0", "items": [], "updated_at": utc_now_iso()}
    return read_json(path)


def build_pkm(*, layout: Layout, module_id: str | None = None, top_k: int = 5) -> dict[str, Any]:
    events = query_events(layout=layout, limit=1000, event_type="verify.passed", module_id=module_id)
    cmd_counter: Counter[str] = Counter()
    event_map: dict[str, list[str]] = {}
    module_map: dict[str, str | None] = {}

    for event in events:
        payload = event.get("payload", {})
        cmd = payload.get("cmd")
        if cmd is None:
            commands = payload.get("commands", [])
            if isinstance(commands, list) and commands:
                cmd = " && ".join(
                    " ".join(item.get("argv", [])) if isinstance(item, dict) else str(item) for item in commands
                )
        if not cmd:
            continue
        cmd_s = str(cmd)
        cmd_counter[cmd_s] += 1
        event_map.setdefault(cmd_s, []).append(str(event["id"]))
        module_map[cmd_s] = event.get("module_id")

    existing = _load_items(layout)
    existing_by_id = {str(item.get("id")): item for item in existing.get("items", [])}
    items: list[dict[str, Any]] = []
    now = utc_now_iso()

    for index, (cmd, freq) in enumerate(cmd_counter.most_common(top_k), start=1):
        item_id = f"PKM-{index:04d}"
        prev = existing_by_id.get(item_id)
        status = "pkm.item.created" if prev is None else "pkm.item.updated"
        confidence = min(0.95, 0.5 + (freq * 0.1))
        item = {
            "id": item_id,
            "kind": "runbook.fact",
            "module_id": module_map.get(cmd),
            "claim": f"Use `{cmd}` for verify in this repository.",
            "command": cmd,
            "confidence": round(confidence, 2),
            "staleness": 0.1,
            "fingerprint": {"git_head": None, "paths": []},
            "justifications": event_map.get(cmd, [])[:20],
            "updated_at": now,
        }
        items.append(item)
        append_event(
            layout=layout,
            event_type=status,
            actor="engine",
            module_id=item.get("module_id"),
            payload={"item_id": item_id, "command": cmd, "confidence": item["confidence"]},
            artifact_refs=[str(_pkm_path(layout))],
        )

    payload = {"schema_version": "1.0.0", "items": items, "updated_at": now}
    ensure_dir(_pkm_path(layout).parent)
    write_json(_pkm_path(layout), payload)
    return {"status": "ok", "items_written": len(items), "path": str(_pkm_path(layout))}
