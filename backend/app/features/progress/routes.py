from fastapi import APIRouter, Depends
from app.api.deps import current_student, get_session, owned_goal
from app.contracts.domain import AttemptBatch, ProgressCommand
from app.core.errors import not_implemented
router = APIRouter(tags=["progress"])


@router.post("/goals/{goal_id}/progress-events")
def event(goal_id: str, body: ProgressCommand, student=Depends(current_student), session=Depends(get_session)):
    owned_goal(session, goal_id, student["id"])
    not_implemented("D: completion and missed events")


@router.post("/goals/{goal_id}/attempt-batches")
def attempts(goal_id: str, body: AttemptBatch, student=Depends(current_student), session=Depends(get_session)):
    owned_goal(session, goal_id, student["id"])
    not_implemented("D: reviewed assessment and evidence")


@router.get("/goals/{goal_id}/questions")
def questions(goal_id: str, student=Depends(current_student), session=Depends(get_session)):
    owned_goal(session, goal_id, student["id"])
    not_implemented("D: reviewed question selection")


@router.get("/goals/{goal_id}/learning-state")
def state(goal_id: str, student=Depends(current_student), session=Depends(get_session)):
    owned_goal(session, goal_id, student["id"])
    not_implemented("D: learner state projection")
