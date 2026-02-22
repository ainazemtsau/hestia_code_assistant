"""Wizard domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WizardOption:
    """Single option shown in a wizard step."""

    value: str
    label: str
    description: str

    def to_dict(self) -> dict[str, str]:
        return {
            "value": self.value,
            "label": self.label,
            "description": self.description,
        }


@dataclass(frozen=True)
class WizardStep:
    """Wizard step metadata."""

    step_id: str
    title: str
    prompt: str
    input_hint: str
    options: list[WizardOption] = field(default_factory=list)
    recommended: str | None = None
    unchanged: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "title": self.title,
            "prompt": self.prompt,
            "input_hint": self.input_hint,
            "options": [opt.to_dict() for opt in self.options],
            "recommended": self.recommended,
            "unchanged": self.unchanged,
        }


@dataclass
class WizardSession:
    """Persisted wizard session state."""

    session_id: str
    status: str
    current_step_index: int
    steps: list[WizardStep]
    context: dict[str, Any]
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "status": self.status,
            "current_step_index": self.current_step_index,
            "steps": [step.to_dict() for step in self.steps],
            "context": self.context,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @property
    def is_completed(self) -> bool:
        return self.status in {"completed", "cancelled"}

    @property
    def current_step(self) -> WizardStep | None:
        if self.current_step_index >= len(self.steps):
            return None
        return self.steps[self.current_step_index]
