"""Wizard step definitions."""

from __future__ import annotations

from csk_next.wizard.models import WizardOption, WizardStep


def wizard_steps() -> list[WizardStep]:
    """Return the ordered wizard step list for v1 planning flow."""
    return [
        WizardStep(
            step_id="intake_request",
            title="Intake",
            prompt="Describe the task/spec in plain language.",
            input_hint="Free text task description.",
            unchanged=["No code changes yet", "No modules created automatically"],
        ),
        WizardStep(
            step_id="module_mapping",
            title="Module Mapping",
            prompt=(
                "Provide module mapping as comma-separated `module_id:path` pairs. "
                "Existing modules can be passed as `module_id` only."
            ),
            input_hint="Example: app:modules/app,api:services/api",
            unchanged=["No module autodetect", "Only explicit module choices are used"],
        ),
        WizardStep(
            step_id="execution_shape",
            title="Execution Shape",
            prompt="Choose task shape.",
            input_hint="single | multi | auto",
            options=[
                WizardOption("single", "Single Module Task", "Run one module task flow."),
                WizardOption("multi", "Multi Module Mission", "Create mission + milestone + module tasks."),
                WizardOption("auto", "Auto from Intake", "Use intake classification to select shape."),
            ],
            recommended="auto",
            unchanged=["Scope remains limited to selected modules"],
        ),
        WizardStep(
            step_id="planning_option",
            title="Planning Option",
            prompt="Choose planning strategy variant.",
            input_hint="A | B | C",
            options=[
                WizardOption("A", "Minimal", "Smaller change set, lower delivery risk."),
                WizardOption("B", "Balanced", "Default balance of scope and risk."),
                WizardOption("C", "Comprehensive", "Broader scope, higher validation demand."),
            ],
            recommended="B",
            unchanged=["Phase gates remain mandatory regardless of option"],
        ),
        WizardStep(
            step_id="confirm_materialization",
            title="Confirmation",
            prompt="Confirm artifact materialization.",
            input_hint="yes | no",
            options=[
                WizardOption("yes", "Proceed", "Create mission/task artifacts now."),
                WizardOption("no", "Cancel", "Stop without creating new task/mission artifacts."),
            ],
            recommended="yes",
            unchanged=["User still controls final approvals and git operations"],
        ),
    ]
