"""
Feature E: Saved-data adapter for loading plans, verifying ownership,
and constructing WorkItemContext from persisted SQLite records.

Pure read-only queries against Base.metadata.tables.
Never mutates the database.
Enforces that caller student owns the goal before returning any plan information.
Unknown or unowned plan IDs both result in 404 PLAN_NOT_FOUND.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.contracts.domain import (
    ActivityResult,
    DeferredWork,
    PlanEntry,
    PlanMetrics,
    PlanSnapshot,
)
from app.core.errors import AppError
from app.db.models import Base
from app.features.insights.service import WorkItemContext

T = Base.metadata.tables


def load_plan_snapshot(session: Session, plan_id: str, student_id: str) -> tuple[PlanSnapshot, str]:
    """
    Load a saved PlanSnapshot from the database while verifying student ownership.
    Returns (PlanSnapshot, goal_id).
    Raises AppError("PLAN_NOT_FOUND", ..., 404) if plan does not exist or belongs to another student.
    Never fabricates topic_id or activity_kind; fails safely with AppError("DATA_INTEGRITY_ERROR", 500)
    if saved data is corrupted/malformed.
    """
    # 1. Join plan_versions and goals to verify ownership atomically
    query = (
        select(
            T["plan_versions"],
            T["goals"].c.student_id.label("owner_student_id"),
            T["students"].c.input_revision.label("student_input_revision"),
        )
        .select_from(
            T["plan_versions"]
            .join(T["goals"], T["plan_versions"].c.goal_id == T["goals"].c.id)
            .join(T["students"], T["goals"].c.student_id == T["students"].c.id)
        )
        .where(T["plan_versions"].c.id == plan_id)
    )
    row = session.execute(query).mappings().first()
    if row is None or row["owner_student_id"] != student_id:
        # Uniform 404 for unknown or unowned plan ID
        raise AppError("PLAN_NOT_FOUND", "Plan was not found.", 404)

    # 2. Load scheduled entries from plan_entries
    entry_rows = (
        session.execute(
            select(T["plan_entries"])
            .where(T["plan_entries"].c.plan_id == plan_id)
            .order_by(T["plan_entries"].c.study_date, T["plan_entries"].c.sequence)
        )
        .mappings()
        .all()
    )

    # 3. Join with work_items to get verified work item metadata (topic_id, kind)
    work_item_ids = [e["work_item_id"] for e in entry_rows]
    work_items_map = {}
    if work_item_ids:
        wi_rows = (
            session.execute(
                select(T["work_items"]).where(T["work_items"].c.id.in_(work_item_ids))
            )
            .mappings()
            .all()
        )
        for w in wi_rows:
            work_items_map[w["id"]] = w

    entries: list[PlanEntry] = []
    for er in entry_rows:
        try:
            act_dict = json.loads(er["activity_json"])
            activity = ActivityResult(**act_dict)
            reason_details = json.loads(er["reason_details_json"])
        except Exception as exc:
            raise AppError("DATA_INTEGRITY_ERROR", "Saved plan entry contains malformed payload.", 500) from exc

        wi_meta = work_items_map.get(er["work_item_id"])
        # PART A RULE 1: Never substitute topic_id="" or activity_kind="learn" when work-item metadata is missing
        if not wi_meta or not wi_meta.get("topic_id") or not wi_meta.get("kind"):
            raise AppError(
                "DATA_INTEGRITY_ERROR",
                f"Work item {er['work_item_id']} is missing verified metadata.",
                500,
            )

        topic_id = wi_meta["topic_id"]
        kind = wi_meta["kind"]

        try:
            entries.append(
                PlanEntry(
                    entry_id=er["id"],
                    work_item_id=er["work_item_id"],
                    topic_id=topic_id,
                    activity_kind=kind,
                    date=date.fromisoformat(er["study_date"]),
                    sequence=er["sequence"],
                    duration_minutes=er["duration_minutes"],
                    activity=activity,
                    reason_code=er["reason_code"],
                    reason_details=reason_details,
                )
            )
        except Exception as exc:
            raise AppError("DATA_INTEGRITY_ERROR", "Saved plan entry violates domain contract.", 500) from exc

    # 4. Parse deferred work from plan_versions.deferred_json
    try:
        raw_deferred = json.loads(row["deferred_json"]) if row["deferred_json"] else []
        deferred = [DeferredWork(**d) for d in raw_deferred]
    except Exception as exc:
        raise AppError("DATA_INTEGRITY_ERROR", "Saved plan contains malformed deferred payload.", 500) from exc

    # 5. Parse metrics and assumptions
    try:
        metrics_dict = json.loads(row["metrics_json"]) if row["metrics_json"] else {}
        metrics = PlanMetrics(**metrics_dict)
        assumptions = json.loads(row["assumptions_json"]) if row["assumptions_json"] else []
    except Exception as exc:
        raise AppError("DATA_INTEGRITY_ERROR", "Saved plan contains malformed metrics or assumptions.", 500) from exc

    # 6. Staleness: Compare plan's input_revision with the student's current input_revision
    # Do NOT equate an older plan version with is_stale; staleness strictly relates to input revision.
    current_rev = row["student_input_revision"]
    is_stale = row["input_revision"] < current_rev

    # Count origins from entries
    origin_counts: dict[str, int] = {}
    for e in entries:
        origin_counts[e.activity.origin] = origin_counts.get(e.activity.origin, 0) + 1

    try:
        created_at_dt = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
    except Exception as exc:
        raise AppError("DATA_INTEGRITY_ERROR", "Saved plan contains invalid created_at timestamp.", 500) from exc

    # 7. PART A RULE 4: Completed history
    # Load actual completed events for this student and goal that occurred up to the plan's creation time
    completed_rows = (
        session.execute(
            select(T["progress_events"])
            .where(
                and_(
                    T["progress_events"].c.student_id == student_id,
                    T["progress_events"].c.goal_id == row["goal_id"],
                    T["progress_events"].c.event_type == "completed",
                    T["progress_events"].c.occurred_at <= row["created_at"],
                )
            )
            .order_by(T["progress_events"].c.occurred_at)
        )
        .mappings()
        .all()
    )
    completed_history = [
        {
            "event_id": cr["id"],
            "work_item_id": cr["work_item_id"],
            "plan_id": cr["plan_id"],
            "occurred_at": cr["occurred_at"],
            "actual_minutes": cr["actual_minutes"],
        }
        for cr in completed_rows
    ]

    try:
        snapshot = PlanSnapshot(
            plan_id=row["id"],
            goal_id=row["goal_id"],
            version=row["version"],
            parent_plan_id=row["parent_plan_id"],
            input_revision=row["input_revision"],
            current_revision=current_rev,
            is_stale=is_stale,
            algorithm_version=row["algorithm_version"],
            policy_version=row["policy_version"],
            created_at=created_at_dt,
            feasibility=row["feasibility"],
            generation_status=row["generation_status"],
            origin_counts=origin_counts,
            metrics=metrics,
            entries=entries,
            deferred=deferred,
            completed_history=completed_history,
            assumptions=assumptions,
        )
    except Exception as exc:
        raise AppError("DATA_INTEGRITY_ERROR", "Failed to reconstruct valid PlanSnapshot from database.", 500) from exc

    return snapshot, row["goal_id"]


def build_work_item_contexts(
    session: Session,
    goal_id: str,
    student_id: str,
    parent: PlanSnapshot | None,
    new_plan: PlanSnapshot,
) -> dict[str, WorkItemContext]:
    """
    Build verified WorkItemContext map for all work items involved in parent & new plans.
    - Verified topic_id and activity_kind from work_items table.
    - Verified completion event ID only when progress_event occurred before new plan was created.
    - PART A RULE 2: Scope change is determined by comparing reliable saved parent and new input snapshots.
      Does not use today's goal_topics table to judge past plan scope.
    - PART A RULE 3: reason_details treated as saved planning facts; only verified event references are attached.
    """
    # Collect work items in parent and new plans
    parent_ids = {e.work_item_id for e in parent.entries} | {d.work_item_id for d in parent.deferred} if parent else set()
    new_ids = {e.work_item_id for e in new_plan.entries} | {d.work_item_id for d in new_plan.deferred}
    all_wids = parent_ids | new_ids

    if not all_wids:
        return {}

    # Query work_items metadata
    wi_rows = (
        session.execute(
            select(T["work_items"]).where(
                and_(
                    T["work_items"].c.goal_id == goal_id,
                    T["work_items"].c.id.in_(all_wids),
                )
            )
        )
        .mappings()
        .all()
    )
    wi_map = {r["id"]: r for r in wi_rows}

    # Query completed progress events for this student, goal, and work items
    # Event must have occurred before new_plan was saved
    new_plan_row = (
        session.execute(
            select(T["plan_versions"].c.created_at, T["plan_versions"].c.input_snapshot_json)
            .where(T["plan_versions"].c.id == new_plan.plan_id)
        )
        .mappings()
        .first()
    )
    new_plan_created_at = new_plan_row["created_at"] if new_plan_row else None
    new_input_snapshot_raw = new_plan_row["input_snapshot_json"] if new_plan_row else "{}"

    parent_input_snapshot_raw = "{}"
    if parent:
        parent_plan_row = (
            session.execute(
                select(T["plan_versions"].c.input_snapshot_json).where(T["plan_versions"].c.id == parent.plan_id)
            )
            .mappings()
            .first()
        )
        if parent_plan_row:
            parent_input_snapshot_raw = parent_plan_row["input_snapshot_json"] or "{}"

    event_query = (
        select(T["progress_events"])
        .where(
            and_(
                T["progress_events"].c.student_id == student_id,
                T["progress_events"].c.goal_id == goal_id,
                T["progress_events"].c.event_type == "completed",
                T["progress_events"].c.work_item_id.in_(all_wids),
            )
        )
    )
    if new_plan_created_at:
        event_query = event_query.where(T["progress_events"].c.occurred_at <= new_plan_created_at)

    completed_events = (
        session.execute(event_query.order_by(T["progress_events"].c.occurred_at.desc()))
        .mappings()
        .all()
    )
    completed_event_by_wid = {e["work_item_id"]: e["id"] for e in completed_events}

    # PART A RULE 2: Scope removal from saved input snapshots
    scope_removed_topics: set[str] = set()
    try:
        p_snap = json.loads(parent_input_snapshot_raw) if parent_input_snapshot_raw else {}
        n_snap = json.loads(new_input_snapshot_raw) if new_input_snapshot_raw else {}
        p_targets = {t["topic_id"] for t in p_snap.get("targets", [])} if isinstance(p_snap, dict) else set()
        n_targets = {t["topic_id"] for t in n_snap.get("targets", [])} if isinstance(n_snap, dict) else set()
        # If both snapshots established target sets, a topic present in parent but absent in new was removed
        if p_targets and n_targets is not None:
            scope_removed_topics = p_targets - n_targets
    except Exception:
        scope_removed_topics = set()

    contexts: dict[str, WorkItemContext] = {}
    for wid in all_wids:
        meta = wi_map.get(wid)
        topic_id = meta["topic_id"] if meta else None
        kind = meta["kind"] if meta else None

        completed_ev_id = completed_event_by_wid.get(wid)
        scope_removed = bool(topic_id and topic_id in scope_removed_topics)

        contexts[wid] = WorkItemContext(
            topic_id=topic_id,
            activity_kind=kind,
            completed_event_id=completed_ev_id,
            scope_removed=scope_removed,
            evidence={},
        )

    return contexts
