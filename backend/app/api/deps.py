import hashlib
from typing import Annotated
from fastapi import Depends, Header, Request
from sqlalchemy import select

from app.core.errors import AppError
from app.db.models import Base


def get_session(request: Request):
    if not request.app.state.database.ready():
        raise AppError("DATABASE_NOT_READY", "Run the database migration before using the application.", 503)
    with request.app.state.database.sessions() as session:
        yield session


def current_student(session=Depends(get_session), token: Annotated[str | None, Header(alias="X-Local-Token")] = None):
    if not token or len(token) > 512:
        raise AppError("UNAUTHORIZED", "Start a local profile to continue.", 401)
    students = Base.metadata.tables["students"]
    digest = hashlib.sha256(token.encode()).hexdigest()
    row = session.execute(select(students).where(students.c.client_token_hash == digest)).mappings().first()
    if row is None:
        raise AppError("UNAUTHORIZED", "This local profile is unavailable. Start a new profile.", 401)
    return dict(row)


def idempotency_key(value: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)]):
    return value


def owned_goal(session, goal_id: str, student_id: str):
    table = Base.metadata.tables["goals"]
    row = session.execute(select(table).where(table.c.id == goal_id, table.c.student_id == student_id)).mappings().first()
    if row is None:
        raise AppError("GOAL_NOT_FOUND", "This goal is unavailable.", 404)
    return row
