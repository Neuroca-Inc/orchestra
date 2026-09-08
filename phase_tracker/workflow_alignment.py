from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .domain import WorkflowMode, WorkflowState
from .state_store import StateStore
from .workflow import align_mode, align_position, describe_position


@dataclass(frozen=True)
class AlignmentReceipt:
    state: WorkflowState
    handoff: str
    warning: str | None = None


def _record_event(
    store: StateStore,
    event: dict,
) -> str | None:
    try:
        store.append_event(event)
    except OSError:
        return "The workflow state was saved, but the convenience event journal was not updated."
    return None


def record_alignment(
    project_root: Path,
    current_state: WorkflowState,
    position: str,
) -> AlignmentReceipt:
    previous_position = describe_position(current_state)
    next_state = align_position(current_state, position)
    event_id = uuid.uuid4().hex
    recorded_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    handoff = (
        f"Workflow position manually aligned: {previous_position} → {position}"
    )
    store = StateStore(project_root)
    store.save(next_state)

    warning = _record_event(
        store,
        {
            "event_id": event_id,
            "event_type": "manual_workflow_alignment",
            "recorded_at": recorded_at,
            "workflow_mode": next_state.workflow_mode.value,
            "previous_position": previous_position,
            "next_position": position,
            "handoff": handoff,
            "path": (
                next_state.last_coordinate.relative_path().as_posix()
                if next_state.last_coordinate
                else None
            ),
        },
    )
    return AlignmentReceipt(next_state, handoff, warning)


def record_mode_alignment(
    project_root: Path,
    current_state: WorkflowState,
    mode: WorkflowMode,
) -> AlignmentReceipt:
    previous_mode = current_state.workflow_mode
    next_state = align_mode(current_state, mode)
    event_id = uuid.uuid4().hex
    recorded_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    handoff = (
        f"Workflow mode changed: {previous_mode.value} → {mode.value}. "
        + (
            "Operator now owns frame, construct, attack, audit, and seal."
            if mode == WorkflowMode.OPERATOR_SKIRMISH
            else "Three-agent Operator/Guardian/Auditor routing restored."
        )
    )
    store = StateStore(project_root)
    store.save(next_state)
    warning = _record_event(
        store,
        {
            "event_id": event_id,
            "event_type": "manual_workflow_mode_alignment",
            "recorded_at": recorded_at,
            "previous_mode": previous_mode.value,
            "next_mode": mode.value,
            "handoff": handoff,
            "path": (
                next_state.last_coordinate.relative_path().as_posix()
                if next_state.last_coordinate
                else None
            ),
        },
    )
    return AlignmentReceipt(next_state, handoff, warning)
