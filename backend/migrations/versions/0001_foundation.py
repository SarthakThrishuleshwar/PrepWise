"""Frozen baseline schema. Never edit after shared use; add a new migration."""
from pathlib import Path
import sqlite3
from alembic import op

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    buffer = ""
    sql = Path(__file__).with_suffix(".sql").read_text(encoding="utf-8")
    for line in sql.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            if "PRAGMA foreign_keys" not in buffer:
                op.get_bind().exec_driver_sql(buffer)
            buffer = ""


def downgrade():
    names = "request_receipts jobs plan_changes student_skill_state attempts questions progress_events plan_entries plan_versions work_items availability goal_topics goals resource_embeddings resources skills prerequisites topics curricula students".split()
    for name in names:
        op.drop_table(name)
