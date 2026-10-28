import hashlib
import json
from pathlib import Path
from sqlalchemy import select
from app.core.errors import AppError
from app.db.models import Base

T = Base.metadata.tables
SEED = Path(__file__).resolve().parents[4] / "docs" / "contracts" / "curriculum-seed.json"


def seed_curriculum(session) -> dict:
    data = json.loads(SEED.read_text(encoding="utf-8"))
    cid = data["curriculum"]["id"]
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    existing = session.execute(select(T["curricula"]).where(T["curricula"].c.id == cid)).mappings().first()
    if existing:
        if existing["content_hash"] != digest:
            raise AppError("SEED_VERSION_CONFLICT", "Publish changed curriculum under a new version instead of overwriting it.", 409)
        return {"curriculum_id": cid, "created": False, "draft_questions": len(data["questions"])}
    topics = {item["id"]: item for item in data["topics"]}
    visited, visiting = set(), set()
    def visit(tid):
        if tid not in topics or tid in visiting:
            raise AppError("CURRICULUM_INVALID", "Missing prerequisite or dependency cycle in seed.", 422)
        if tid in visited:
            return
        visiting.add(tid)
        for parent in topics[tid]["prerequisites"]:
            visit(parent)
        visiting.remove(tid)
        visited.add(tid)
    for tid in topics:
        visit(tid)
    session.execute(T["curricula"].insert().values(id=cid, title=data["curriculum"]["title"], version=data["curriculum"]["version"], status="published", content_hash=digest))
    for topic in topics.values():
        session.execute(T["topics"].insert().values(curriculum_id=cid, **{k:v for k,v in topic.items() if k != "prerequisites"}))
    for topic in topics.values():
        for parent in topic["prerequisites"]:
            session.execute(T["prerequisites"].insert().values(curriculum_id=cid, topic_id=topic["id"], prerequisite_topic_id=parent))
    for skill in data["skills"]:
        session.execute(T["skills"].insert().values(curriculum_id=cid, **skill))
    for resource in data["resources"]:
        session.execute(T["resources"].insert().values(curriculum_id=cid, content_hash=hashlib.sha256(resource["body"].encode()).hexdigest(), **resource))
    for question in data["questions"]:
        row = dict(question)
        row["options_json"] = json.dumps(row.pop("options"))
        row["reviewed"] = int(row["reviewed"])
        session.execute(T["questions"].insert().values(**row))
    return {"curriculum_id": cid, "created": True, "draft_questions": len(data["questions"])}


def curriculum_snapshot(session, cid):
    row = session.execute(select(T["curricula"]).where(T["curricula"].c.id == cid, T["curricula"].c.status == "published")).mappings().first()
    if row is None:
        raise AppError("CURRICULUM_NOT_FOUND", "Choose an available curriculum.", 404)
    return {"curriculum_id": row["id"], "title": row["title"], "version": row["version"], "content_hash": row["content_hash"],
            "topics": [dict(x) for x in session.execute(select(T["topics"]).where(T["topics"].c.curriculum_id == cid).order_by(T["topics"].c.position)).mappings()],
            "prerequisites": [dict(x) for x in session.execute(select(T["prerequisites"]).where(T["prerequisites"].c.curriculum_id == cid)).mappings()]}
