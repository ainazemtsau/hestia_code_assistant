"""Intake classification and discovery draft generation."""

from __future__ import annotations

from typing import Any

from csk_next.domain.models import intake_stub


def classify_request(request: str, module_candidates: list[str]) -> dict[str, Any]:
    payload = intake_stub(request)
    payload["routing_draft"] = [
        {
            "module_id": module_id,
            "reason": "Selected during initial root-level routing draft.",
        }
        for module_id in module_candidates
    ]
    payload["preserved_areas"] = ["Unrelated modules", "Deployment setup"]
    return payload
