# 05 — Local database design

## 1. Storage decision and invariants

Use one SQLite file via SQLAlchemy. This supports the local single-host prototype without a separate database server. The [reference DDL](reference/schema.sql) defines relational constraints and indexes; foundation translates it to a reviewed baseline Alembic migration. Do not treat SQL script execution as evidence that ORM or API code exists.

Global invariants:

1. Every authenticated mutation belongs to the token-derived student.
2. Goal topics, work items, resources and prerequisites belong to their curriculum.
3. At most one active plan per goal and one queued/running job per student.
4. Old plan entries remain immutable after activation.
5. Work-item completion and question attempts are distinct evidence.
6. Every accepted data change increments student.input_revision once.
7. Active plan input_revision may lag current revision; this is exposed as stale.
8. No model call occurs inside a write transaction.

## 2. Entity model

~~~mermaid
erDiagram
    STUDENTS ||--o{ GOALS : owns
    CURRICULA ||--o{ TOPICS : contains
    TOPICS ||--o{ SKILLS : decomposes
    TOPICS ||--o{ RESOURCES : supports
    RESOURCES ||--o{ RESOURCE_EMBEDDINGS : indexed_by
    GOALS ||--o{ GOAL_TOPICS : selects
    GOALS ||--o{ AVAILABILITY : budgets
    GOALS ||--o{ WORK_ITEMS : requires
    GOALS ||--o{ PLAN_VERSIONS : versions
    PLAN_VERSIONS ||--o{ PLAN_ENTRIES : schedules
    WORK_ITEMS ||--o{ PLAN_ENTRIES : appears_in
    WORK_ITEMS ||--o{ PROGRESS_EVENTS : records
    SKILLS ||--o{ QUESTIONS : assesses
    QUESTIONS ||--o{ ATTEMPTS : answered
    STUDENTS ||--o{ STUDENT_SKILL_STATE : estimates
    PLAN_VERSIONS ||--o{ PLAN_CHANGES : explains
    GOALS ||--o{ JOBS : generates
    STUDENTS ||--o{ REQUEST_RECEIPTS : deduplicates
~~~

## 3. Data dictionary

| Table | Meaning and important policy |
|---|---|
| students | Local identity token hash, timezone, optional nickname and global input_revision |
| curricula | Immutable published curriculum version; title, content hash |
| topics | Curriculum objective, difficulty 1–5, importance 0–1, estimated learn/practice/check minutes |
| prerequisites | Directed topic dependency, same curriculum; cycle detection remains application logic |
| skills | Assessed micro-skills belonging to one topic |
| resources | Reviewed source text associated with one curriculum/topic |
| resource_embeddings | Per-resource fingerprint, content hash, dimension and numeric vector JSON |
| goals | Student-selected curriculum, inclusive horizon, title and goal text |
| goal_topics | Explicit targets and optional self-report; does not contain inferred prerequisite closure |
| availability | Actual per-date capacity, including zero days |
| work_items | Stable units of required effort; identity survives plan versions |
| plan_versions | Immutable sanitized input snapshot/revision/hash, policy, estimates, deferred work, status |
| plan_entries | Version-specific placement and activity snapshot for a work item |
| progress_events | Append-only occurrence reports; work-item state is a projection |
| questions | Reviewed item, one assessed skill, options and private answer key |
| attempts | Submitted answers, server correctness, hint count, evidence eligibility |
| student_skill_state | Rebuildable projection from attempts, not independent source of truth |
| plan_changes | Before/after placements and evidence-backed reasons |
| jobs | Persisted status and result pointer; no automatic restart execution |
| request_receipts | Atomic idempotency response cache for authenticated mutations |

JSON columns hold bounded snapshots, not relationships we need to join. Topics, goals, attempts, session identity and resource IDs have relational records. Deferred JSON stores item IDs/minutes/reason and is validated against the candidate. Source resource references inside activity JSON are validated in application code.

input_snapshot_json records the decision inputs needed to inspect an old version after the goal changes: target IDs, dated capacities, self-reports, curriculum hash, completed unit IDs, evidence summaries/attempt references, effective local date and parent plan. Exclude identity token and nickname. A hash alone cannot reconstruct an earlier goal. Curriculum versions and attempt/event history remain immutable references.

## 4. Stable work identity

Use unit_key such as topic_id:learn:01 or skill_id:repair:policy-v1:01. Unique(goal_id, unit_key) prevents creating new identities on each replan. Adaptation rules upsert missing units by this key. Completed units are never made pending by planning.

The same work_item_id can appear in several plan versions with different dates or bounded estimated durations. The old plan entry keeps its original duration and activity. A current pending unit is not necessarily scheduled in the current partial plan; deferred items stay in the required-work set.

A repair is one persistent unit for the current policy cycle. Repeated failure does not create unlimited copies on every click. Future multiple remediation cycles require explicit versioned cycle keys and limits.

## 5. Transaction recipes

### Goal or availability write

Check ownership and receipt; compare expected_revision; validate horizon/targets; write normalized rows; increment input_revision; insert receipt; commit. Do not update old plan entries. A later GET computes is_stale.

### Completion/missed event

Check active plan ownership and occurrence; check receipt; check revision; prevent completed → missed; insert event only if new occurrence; update work_item state; increment revision only on a genuine event; write receipt; commit. Replayed/no-op completion does not count time twice.

### Assessment batch

Check ownership/curriculum; load private reviewed keys; determine first-ever-attempt eligibility; insert attempts; recompute affected skill projection from eligible attempts; increment revision once for the batch; write receipt; commit. A later unhinted retry of an already-seen item is not independent evidence.

### Plan activation

Read/infer outside write transaction. In final short transaction: compare input_revision to accepted revision, confirm base is still active, upsert required work items, insert candidate version/entries/differences, supersede old active version, activate candidate, complete job with result pointer, commit. Any violation rolls everything back. Never leave a goal with two active versions. Candidate work-item upserts must occur only after stale checks.

## 6. Constraints beyond SQL

Application must check DAG cycles; horizon lengths; date validity/timezone; daily total minutes; prerequisite ordering; same curriculum for question and goal; selected option belongs to question; JSON resource IDs exist; parent plan is active when replanning; and model output semantics.

Database composite foreign keys prevent many cross-curriculum/cross-goal errors but do not replace ownership checks. The active-plan and active-job partial unique indexes are final concurrency defenses.

SQLite connection setup must enable foreign keys per connection. busy_timeout handles short contention, not unlimited write concurrency. WAL is a local initialization decision; apply it outside an active transaction. Migration/constraint behavior should be tested against the event Python/SQLite version [S03].

## 7. Curriculum, vector and question lifecycle

Published curriculum versions are immutable. Edit a draft or publish a new curriculum ID/version rather than changing content underneath saved plans. Change resource content_hash when text changes; cached embeddings with mismatched hash/fingerprint/dimension cannot be queried. No vector service is needed for the reviewed prototype corpus.

Question edits after attempts exist need a new question ID. Different wording of the same item is not automatically independent: seed authors must identify genuinely comparable alternate items. Protect answer keys in API serialization.

## 8. Persistence, backup and evolution

Keep real DB/cache files out of source control. Include synthetic seed definitions and migrations. Re-running seed must be idempotent and must not reset student progress. A destructive demo reset must be a separately named developer action, never normal startup.

Use SQLite's backup API for a live backup, or stop the app before copying the file; do not copy only the main file while WAL writes are active. Local demo retains data until explicit developer cleanup. Multi-user authentication, retention controls and hosted backup policy are production prerequisites outside this event scope.

Move to PostgreSQL when concurrent writers or hosted users justify it. Repositories and service DTOs remain stable; port migration types/indexes and rerun invariants. No claim of production readiness is made by using a relational database.
