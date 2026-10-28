from fastapi import APIRouter, Depends
from app.api.deps import current_student
from app.core.errors import not_implemented
router = APIRouter(tags=["insights"])


@router.get("/plans/{plan_id}/changes")
def changes(plan_id: str, student=Depends(current_student)):
    not_implemented("E: version comparison")


@router.get("/plans/{plan_id}/export")
def export(plan_id: str, student=Depends(current_student)):
    not_implemented("E: version-specific exports")
