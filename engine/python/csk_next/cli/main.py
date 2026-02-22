"""CSK CLI entrypoint."""

from __future__ import annotations

import argparse
import json
from typing import Any, Callable

from csk_next.cli.parser import build_parser


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handler: Callable[[argparse.Namespace], dict[str, Any]] = args.handler
    try:
        payload = handler(args)
    except Exception as exc:  # noqa: BLE001
        payload = {"status": "error", "error": str(exc)}
        _print(payload)
        return 1

    _print(payload)
    failure_statuses = {"error", "failed", "gate_failed", "review_failed", "blocked"}
    return 0 if payload.get("status") not in failure_statuses else 1


if __name__ == "__main__":
    raise SystemExit(main())
