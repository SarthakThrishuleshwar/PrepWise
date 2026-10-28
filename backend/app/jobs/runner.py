from datetime import datetime, timezone
from sqlalchemy import select, update
from app.core.errors import AppError
from app.db.models import Base

T = Base.metadata.tables


class JobRunner:
    """Shared lifecycle. B supplies a handler that atomically activates a valid plan."""
    def __init__(self, database):
        self.database = database

    def recover(self) -> int:
        with self.database.sessions.begin() as session:
            result = session.execute(update(T["jobs"]).where(T["jobs"].c.status.in_(["queued", "running"])).values(status="interrupted", error_code="JOB_INTERRUPTED", error_message="Application restarted; retry explicitly.", finished_at=datetime.now(timezone.utc).isoformat()))
            return result.rowcount

    def run(self, job_id: str, handler):
        with self.database.sessions.begin() as session:
            claimed = session.execute(update(T["jobs"]).where(T["jobs"].c.id == job_id, T["jobs"].c.status == "queued").values(status="running", stage="snapshot"))
            if claimed.rowcount != 1:
                return
        try:
            handler(job_id)  # independent sessions; never run inference inside this runner's transaction
            with self.database.sessions() as session:
                status = session.execute(select(T["jobs"].c.status).where(T["jobs"].c.id == job_id)).scalar_one()
                if status != "completed":
                    raise AppError("JOB_HANDLER_INCOMPLETE", "The handler did not save a completed plan.", 500)
        except Exception as exc:
            code = exc.code if isinstance(exc, AppError) else "JOB_FAILED"
            with self.database.sessions.begin() as session:
                session.execute(update(T["jobs"]).where(T["jobs"].c.id == job_id, T["jobs"].c.status == "running").values(status="failed", error_code=code, error_message="Plan generation did not complete. Your saved inputs remain available.", finished_at=datetime.now(timezone.utc).isoformat()))

    @staticmethod
    def complete(session, job_id: str, plan_id: str):
        job = session.execute(select(T["jobs"]).where(T["jobs"].c.id == job_id, T["jobs"].c.status == "running")).mappings().one()
        revision = session.execute(select(T["students"].c.input_revision).where(T["students"].c.id == job["student_id"])).scalar_one()
        if revision != job["accepted_revision"]:
            raise AppError("STALE_INPUT", "Newer progress exists; retry with current inputs.", 409)
        plan = session.execute(select(T["plan_versions"]).where(T["plan_versions"].c.id == plan_id, T["plan_versions"].c.goal_id == job["goal_id"], T["plan_versions"].c.input_revision == revision, T["plan_versions"].c.status == "active")).first()
        if not plan:
            raise AppError("INVALID_PLAN_RESULT", "A valid active result must be saved before completing a job.", 500)
        session.execute(update(T["jobs"]).where(T["jobs"].c.id == job_id).values(status="completed", stage="done", result_plan_id=plan_id, finished_at=datetime.now(timezone.utc).isoformat()))
