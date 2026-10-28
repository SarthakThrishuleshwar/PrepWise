from fastapi import APIRouter, Depends
from sqlalchemy import select
from app.api.deps import get_session
from app.contracts.domain import CurriculumSnapshot
from app.db.models import Base
from app.features.curriculum.service import curriculum_snapshot

router = APIRouter(tags=["curriculum"])


@router.get("/curricula")
def list_curricula(session=Depends(get_session)):
    table = Base.metadata.tables["curricula"]
    return [dict(row) for row in session.execute(select(table.c.id, table.c.title, table.c.version).where(table.c.status == "published")).mappings()]


@router.get("/curricula/{curriculum_id}", response_model=CurriculumSnapshot)
def get_curriculum(curriculum_id: str, session=Depends(get_session)):
    return curriculum_snapshot(session, curriculum_id)
