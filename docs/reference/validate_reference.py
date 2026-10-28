"""Validate documentation reference artifacts, not the unimplemented application."""
import hashlib
import json
import re
import sqlite3
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
CONTRACTS = DOCS / "contracts"


def load(name):
    return json.loads((CONTRACTS / name).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def check_links():
    files = [ROOT / "README.md", *DOCS.rglob("*.md")]
    count = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        fences = [line for line in text.splitlines() if line.startswith("~~~")]
        require(len(fences) % 2 == 0, f"Unbalanced code fence: {path}")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if target.startswith(("https://", "http://", "#")):
                continue
            local = target.split("#", 1)[0]
            require((path.parent / local).exists(), f"Broken link: {path}: {target}")
            count += 1
    return len(files), count


def check_curriculum(seed):
    topics = {row["id"]: row for row in seed["topics"]}
    require(len(topics) == len(seed["topics"]), "Duplicate topic IDs")
    visited, visiting = set(), set()

    def visit(tid):
        require(tid in topics, f"Unknown prerequisite {tid}")
        require(tid not in visiting, f"Dependency cycle at {tid}")
        if tid in visited:
            return
        visiting.add(tid)
        for parent in topics[tid]["prerequisites"]:
            visit(parent)
        visiting.remove(tid)
        visited.add(tid)

    for tid in topics:
        visit(tid)
    skills = {row["id"]: row for row in seed["skills"]}
    resources = {row["id"]: row for row in seed["resources"]}
    for skill in skills.values():
        require(skill["topic_id"] in topics, "Unknown skill topic")
    for resource in resources.values():
        require(resource["topic_id"] in topics, "Unknown resource topic")
    for q in seed["questions"]:
        require(q["skill_id"] in skills, "Unknown question skill")
        require(q["answer_option"] in q["options"], "Unknown correct option")
        require(q["reviewed"] is False, "Draft seed must not silently be approved")
    return topics, skills, resources


def check_answer_calculations(seed):
    def accumulate(initial, values, operation):
        result = initial
        for value in values:
            result = operation(result, value)
        return result

    expected = {
        "range-b1": list(range(1, 4)), "range-b2": len(range(2, 5)),
        "range-b3": list(range(3)), "range-f1": list(range(4, 7)),
        "range-f2": len(range(8, 11)), "range-f3": list(range(7, 10)),
        "acc-b1": accumulate(0, range(1, 4), lambda a, i: a + i),
        "acc-b2": accumulate(2, range(3), lambda a, i: a + 2),
        "acc-b3": accumulate(1, range(1, 4), lambda a, i: a * 2),
        "acc-f1": accumulate(0, range(2, 5), lambda a, i: a + i),
        "acc-f2": accumulate(3, range(2), lambda a, i: a + 4),
        "acc-f3": accumulate(1, range(3), lambda a, i: a * 3),
        "list-b1": [10, 20, 30][0], "list-b2": ["red", "blue", "green"][2],
        "list-b3": len([4, 8]), "list-f1": [7, 9, 11][1],
        "list-f2": [2, 4, 6][-1], "list-f3": len(["a", "b", "c", "d"]),
    }
    for q in seed["questions"]:
        require(q["options"][q["answer_option"]] == str(expected[q["id"]]),
                f"Incorrect reference key: {q['id']}")


def check_plan(seed, goal, plan, topics, resources):
    capacities = {row["date"]: row["minutes"] for row in goal["availability"]}
    require(len(capacities) == len(goal["availability"]), "Duplicate availability date")
    start, end = date.fromisoformat(goal["start_date"]), date.fromisoformat(goal["deadline"])
    require(1 <= (end - start).days + 1 <= 30, "Bad horizon")
    selected = {row["topic_id"] for row in goal["targets"]}
    closure = set()

    def collect(tid):
        if tid not in closure:
            closure.add(tid)
            for parent in topics[tid]["prerequisites"]:
                collect(parent)
    for tid in selected:
        collect(tid)
    expected_minutes = sum(topics[t][key] for t in closure
                           for key in ("learn_minutes", "practice_minutes", "check_minutes"))
    totals, places, seen = {}, {}, set()
    for entry in plan["entries"]:
        tid, day, minutes = entry["topic_id"], entry["date"], entry["duration_minutes"]
        require(entry["work_item_id"] not in seen, "Duplicate work item")
        seen.add(entry["work_item_id"])
        require(tid in closure, "Entry outside target closure")
        require(start <= date.fromisoformat(day) <= end, "Entry outside horizon")
        require(minutes > 0, "Nonpositive entry")
        totals[day] = totals.get(day, 0) + minutes
        places.setdefault(tid, []).append((day, entry["sequence"]))
        require(entry["activity"]["steps"], "Missing activity instructions")
        for rid in entry["activity"]["resource_ids"]:
            require(rid in resources and resources[rid]["topic_id"] == tid,
                    "Invalid resource provenance")
    for day, minutes in totals.items():
        require(minutes <= capacities.get(day, 0), f"Overfilled date {day}")
    for tid in closure:
        for parent in topics[tid]["prerequisites"]:
            require(max(places[parent]) < min(places[tid]), "Prerequisite order violation")
    metrics = plan["metrics"]
    scheduled = sum(totals.values())
    require(scheduled == expected_minutes == metrics["remaining_work_minutes"], "Workload mismatch")
    require(scheduled == metrics["scheduled_minutes"], "Scheduled metric mismatch")
    require(metrics["capacity_minutes"] == sum(capacities.values()), "Capacity mismatch")
    require(metrics["deferred_minutes"] == 0 and not plan["deferred"], "Full-plan deferral")
    require(plan["origin_counts"]["template"] == len(plan["entries"]), "Origin mismatch")
    return scheduled


def check_database(seed, goal):
    db = sqlite3.connect(":memory:")
    db.executescript((DOCS / "reference" / "schema.sql").read_text(encoding="utf-8"))
    require(db.execute("PRAGMA foreign_keys").fetchone()[0] == 1, "Foreign keys disabled")
    cid = seed["curriculum"]["id"]
    digest = lambda value: hashlib.sha256(value.encode()).hexdigest()
    db.execute("INSERT INTO curricula VALUES (?,?,?,?,?)", (cid,"Python Foundations","1.0","published",digest("seed")))
    for t in seed["topics"]:
        db.execute("INSERT INTO topics VALUES (?,?,?,?,?,?,?,?,?,?)", (t["id"],cid,t["title"],t["objective"],t["difficulty"],t["importance"],t["learn_minutes"],t["practice_minutes"],t["check_minutes"],t["position"]))
    for t in seed["topics"]:
        for parent in t["prerequisites"]:
            db.execute("INSERT INTO prerequisites VALUES (?,?,?)", (cid,t["id"],parent))
    for s in seed["skills"]:
        db.execute("INSERT INTO skills VALUES (?,?,?,?,?)", (s["id"],cid,s["topic_id"],s["title"],s["objective"]))
    for r in seed["resources"]:
        db.execute("INSERT INTO resources VALUES (?,?,?,?,?,?,?)", (r["id"],cid,r["topic_id"],r["title"],r["body"],r["source_label"],digest(r["body"])))
    for q in seed["questions"]:
        db.execute("INSERT INTO questions VALUES (?,?,?,?,?,?,?,?,?)", (q["id"],q["skill_id"],q["prompt"],json.dumps(q["options"]),q["answer_option"],q["explanation"],q["difficulty"],q["form"],int(q["reviewed"])))
    db.execute("INSERT INTO students(id,client_token_hash) VALUES ('student',?)", (digest("reference-token"),))
    db.execute("INSERT INTO goals VALUES (?,?,?,?,?,?,?)", ("goal","student",cid,goal["title"],goal["goal_text"],goal["start_date"],goal["deadline"]))
    for t in goal["targets"]:
        db.execute("INSERT INTO goal_topics VALUES (?,?,?,?)", ("goal",cid,t["topic_id"],t["self_report"]))
    for a in goal["availability"]:
        db.execute("INSERT INTO availability VALUES (?,?,?)", ("goal",a["date"],a["minutes"]))

    def reject(sql, params=()):
        db.execute("SAVEPOINT negative_check")
        try:
            db.execute(sql, params)
        except sqlite3.IntegrityError:
            db.execute("ROLLBACK TO negative_check")
            db.execute("RELEASE negative_check")
            return
        db.execute("ROLLBACK TO negative_check")
        db.execute("RELEASE negative_check")
        raise AssertionError("Expected constraint rejection: " + sql)

    reject("INSERT INTO availability VALUES ('goal','2026-10-28',-1)")
    reject("INSERT INTO prerequisites VALUES (?, 'loops', 'missing')", (cid,))
    reject("INSERT INTO prerequisites VALUES (?, 'loops', 'loops')", (cid,))
    db.execute("INSERT INTO jobs(id,student_id,goal_id,mode,status,stage,accepted_revision,request_id) VALUES ('job1','student','goal','generate','queued','accepted',0,'req1')")
    reject("INSERT INTO jobs(id,student_id,goal_id,mode,status,stage,accepted_revision,request_id) VALUES ('job2','student','goal','generate','queued','accepted',0,'req2')")
    plan_sql = "INSERT INTO plan_versions(id,goal_id,version,status,input_revision,algorithm_version,policy_version,feasibility,generation_status,config_json,metrics_json,deferred_json,assumptions_json,input_snapshot_json,snapshot_hash) VALUES (?, 'goal', ?, 'active',0,'v1','v1','full','template_only','{}','{}','[]','[]','{}','hash')"
    db.execute(plan_sql, ("p1",1))
    reject(plan_sql, ("p2",2))
    require(not db.execute("PRAGMA foreign_key_check").fetchall(), "Foreign key violation")
    count = db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    db.close()
    return count


def main():
    docs, links = check_links()
    paths = list(CONTRACTS.glob("*.json"))
    for path in paths:
        json.loads(path.read_text(encoding="utf-8"))
    seed, goal, plan = load("curriculum-seed.json"), load("goal-create.json"), load("plan-example.json")
    topics, skills, resources = check_curriculum(seed)
    check_answer_calculations(seed)
    scheduled = check_plan(seed,goal,plan,topics,resources)
    tables = check_database(seed,goal)
    attempt = load("attempt-batch.json")
    keys = {q["id"]: q for q in seed["questions"]}
    for item in attempt["items"]:
        require(item["question_id"] in keys, "Unknown attempt question")
        require(item["selected_option"] in keys[item["question_id"]]["options"], "Unknown selected option")
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ModuleNotFoundError:
        schema_status = "optional JSON Schema engine unavailable; skipped"
    else:
        schema = load("goal-create.schema.json")
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema,format_checker=FormatChecker()).validate(goal)
        schema_status = "goal JSON Schema validated"
    print(f"PASS: {docs} Markdown documents, {links} local links, {len(paths)} JSON files")
    print(f"PASS: SQLite {sqlite3.sqlite_version}, {tables} reference tables and selected constraint failures")
    print(f"PASS: {len(topics)} topics, {len(skills)} skills, {len(keys)} calculated answer keys")
    print(f"PASS: reference plan {scheduled} minutes, provenance, capacity and prerequisite accounting")
    print(schema_status)
    print("Scope: reference artifacts only; application checks are recorded separately in document 13.")


if __name__ == "__main__":
    main()
