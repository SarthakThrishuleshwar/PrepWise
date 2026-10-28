from datetime import timedelta
from uuid import uuid4
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from app.api.deps import current_student, get_session, idempotency_key, owned_goal
from app.contracts.domain import AvailabilityReplace, GoalCreate, PlanJobCreate, validate_availability
from app.core.errors import AppError, not_implemented
from app.core.mutations import atomic_write
from app.db.models import Base

router = APIRouter(tags=["planning"])
T = Base.metadata.tables


def goal_response(session, goal_id, student_id):
    row = dict(owned_goal(session, goal_id, student_id))
    row["goal_id"] = row.pop("id")
    row.pop("student_id")
    row["targets"] = [dict(x) for x in session.execute(select(T["goal_topics"].c.topic_id, T["goal_topics"].c.self_report).where(T["goal_topics"].c.goal_id == goal_id)).mappings()]
    row["availability"] = [{"date": x["study_date"], "minutes": x["minutes"]} for x in session.execute(select(T["availability"]).where(T["availability"].c.goal_id == goal_id).order_by(T["availability"].c.study_date)).mappings()]
    row["input_revision"] = session.execute(select(T["students"].c.input_revision).where(T["students"].c.id == student_id)).scalar_one()
    return row


@router.post("/goals", status_code=201)
def create_goal(body: GoalCreate, request: Request, student=Depends(current_student), session=Depends(get_session), key=Depends(idempotency_key)):
    def operation(db, revision):
        curriculum = db.execute(select(T["curricula"]).where(T["curricula"].c.id == body.curriculum_id, T["curricula"].c.status == "published")).first()
        if not curriculum:
            raise AppError("CURRICULUM_NOT_FOUND", "Choose an available curriculum.", 422)
        allowed = set(db.execute(select(T["topics"].c.id).where(T["topics"].c.curriculum_id == body.curriculum_id)).scalars())
        if any(t.topic_id not in allowed for t in body.targets):
            raise AppError("CURRICULUM_MISMATCH", "Choose target topics from the selected curriculum.", 422)
        gid = str(uuid4())
        db.execute(T["goals"].insert().values(id=gid, student_id=student["id"], curriculum_id=body.curriculum_id, title=body.title, goal_text=body.goal_text, start_date=body.start_date.isoformat(), deadline=body.deadline.isoformat()))
        for target in body.targets:
            db.execute(T["goal_topics"].insert().values(goal_id=gid, curriculum_id=body.curriculum_id, topic_id=target.topic_id, self_report=target.self_report.value))
        capacities = {row.date: row.minutes for row in body.availability}
        for offset in range((body.deadline-body.start_date).days+1):
            day = body.start_date + timedelta(days=offset)
            db.execute(T["availability"].insert().values(goal_id=gid, study_date=day.isoformat(), minutes=capacities.get(day, 0)))
        return 201, goal_response(db, gid, student["id"])
    status, result = atomic_write(session, student["id"], key, "POST", request.url.path, body.model_dump(mode="json"), body.expected_revision, operation)
    return JSONResponse(result, status_code=status)


@router.get("/goals/{goal_id}")
def get_goal(goal_id: str, student=Depends(current_student), session=Depends(get_session)):
    return goal_response(session, goal_id, student["id"])


@router.put("/goals/{goal_id}/availability")
def replace_availability(goal_id: str, body: AvailabilityReplace, request: Request, student=Depends(current_student), session=Depends(get_session), key=Depends(idempotency_key)):
    def operation(db, revision):
        from datetime import date
        goal = owned_goal(db, goal_id, student["id"])
        start, end = date.fromisoformat(goal["start_date"]), date.fromisoformat(goal["deadline"])
        try:
            validate_availability(body.availability, start, end)
        except ValueError as exc:
            raise AppError("INPUT_INVALID", str(exc), 422) from exc
        db.execute(T["availability"].delete().where(T["availability"].c.goal_id == goal_id))
        capacities = {row.date: row.minutes for row in body.availability}
        for offset in range((end-start).days+1):
            day = start + timedelta(days=offset)
            db.execute(T["availability"].insert().values(goal_id=goal_id, study_date=day.isoformat(), minutes=capacities.get(day,0)))
        return 200, goal_response(db, goal_id, student["id"])
    status, result = atomic_write(session, student["id"], key, "PUT", request.url.path, body.model_dump(mode="json"), body.expected_revision, operation)
    return JSONResponse(result, status_code=status)


@router.patch("/goals/{goal_id}")
def patch_goal(goal_id: str, student=Depends(current_student), session=Depends(get_session)):
    owned_goal(session, goal_id, student["id"])
    not_implemented("B: goal editing")


@router.post("/goals/{goal_id}/plan-jobs", status_code=202)
def create_plan_job(goal_id: str, body: PlanJobCreate, student=Depends(current_student), session=Depends(get_session)):
    owned_goal(session, goal_id, student["id"])
    not_implemented("B: planning agent and job handler")


@router.get("/goals/{goal_id}/plans/current")
def current_plan(goal_id: str, student=Depends(current_student), session=Depends(get_session)):
    owned_goal(session, goal_id, student["id"])
    raise AppError("PLAN_NOT_FOUND", "No plan has been generated for this goal yet.", 404)


@router.get("/plans/{plan_id}")
def get_plan(plan_id: str, student=Depends(current_student)):
    not_implemented("B: saved plan serialization")
