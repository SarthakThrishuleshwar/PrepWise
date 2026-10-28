# 04 — Technical requirements and API contracts

## 1. Contract rules

Base path: /api/v1. JSON uses snake_case. IDs are opaque UUID strings; documentation fixtures may use readable IDs. Dates use YYYY-MM-DD; UTC timestamps use ISO 8601 with Z. Enums are lowercase. DTOs reject unknown write fields. Database rows are not returned directly.

Frontend foundation uses React/TypeScript/Vite and document 12. The API is usable from any selected frontend and from generated OpenAPI. Students never need to see JSON or upload files.

Authenticated routes require X-Local-Token. Derive the student from its stored hash. Never accept client-selected ownership. Token is created once by POST /students, stored by the local application, and is not a production account mechanism.

Authenticated writes require Idempotency-Key (UUID recommended). Hash the validated canonical payload plus method/path. Same student/key/hash returns the saved response without another mutation. Same key with different payload/path returns 409 IDEMPOTENCY_CONFLICT. Check receipts before stale-revision checks so retrying a successful request works. Persist receipt and mutation atomically.

Mutations to goals, availability, events and attempts include expected_revision. Compare/update students.input_revision atomically in the transaction. On mismatch return 409 STALE_REVISION with the current revision. Profile/goal/event/attempt changes increment revision once per accepted request; job creation, reads and generated plan activation do not increment it.

## 2. Routes and ownership

| Method/path | Purpose | Success | Feature owner |
|---|---|---|---|
| GET /health | Process and schema readiness, no secrets | 200 | Foundation |
| GET /capabilities | Configured model IDs, availability, feature flags; private host details omitted | 200 | Foundation |
| POST /students | Create local identity, nickname, timezone; token returned once | 201 | Foundation |
| GET /me | Current profile and input_revision | 200 | Foundation |
| GET /curricula | Published curricula | 200 | A |
| GET /curricula/{id} | Topics, objectives, edges, available assessment coverage | 200 | A |
| POST /goals | Save form-backed selected topics and per-date availability | 201 | B |
| GET /goals/{id} | Saved goal, capacities and current revision | 200 | B |
| PATCH /goals/{id} | Replace specified goal fields; published curriculum cannot change | 200 | B |
| PUT /goals/{id}/availability | Replace entire dated availability map atomically | 200 | B |
| POST /goals/{id}/plan-jobs | Accept generation or replan | 202 | B |
| GET /jobs/{id} | queued/running/completed/failed/interrupted | 200 | Foundation + B |
| GET /goals/{id}/plans/current | Current active plan plus stale flag | 200 | B |
| GET /plans/{id} | Immutable saved plan content plus current progress overlay | 200 | B |
| POST /goals/{id}/progress-events | Record completed or missed atomic work unit | 201 | D |
| GET /goals/{id}/questions?skill_id=...&form=... | Reviewed questions without correct answer/explanation | 200 | D |
| POST /goals/{id}/attempt-batches | Score reviewed attempts atomically | 201 | D |
| GET /goals/{id}/learning-state | Evidence counts, estimates and limitations | 200 | D |
| GET /plans/{id}/changes | Differences against parent version | 200 | E |
| GET /plans/{id}/export?format=csv|json | Version-specific export | 200 | E |

For GET current plan with no saved plan use 404 PLAN_NOT_FOUND, not an empty fabricated plan. Use 404 for resources outside the caller's ownership. A resource ID belonging to another curriculum in a write is a 422 CURRICULUM_MISMATCH.

## 3. Input fields

POST /students: display_name optional (1–80 chars), timezone IANA string default Asia/Kolkata. Return student_id, client_token and input_revision=0. Never return token_hash. A lost token requires a new local identity in MVP; account recovery is deferred.

POST /goals:

~~~json
{
  "expected_revision": 0,
  "curriculum_id": "python-foundations-v1",
  "title": "Prepare programming foundations",
  "goal_text": "Become confident tracing loops",
  "start_date": "2026-10-28",
  "deadline": "2026-11-03",
  "targets": [{"topic_id": "loops", "self_report": "low"}],
  "availability": [{"date": "2026-10-28", "minutes": 60}]
}
~~~

Horizon 1–30 days inclusive in MVP. Missing dates mean zero minutes, not an implied default. Form may expand a weekly pattern into dates before sending. Minutes are integers 0–480. Targets: 1–30 unique published topic IDs. goal_text maximum 1000 chars. self_report enum unknown/low/medium/high. Positive capacity is recommended but zero capacity is a supported saved state. Dates before local today cannot receive new planned entries.

PATCH /goals supports title, goal_text, start_date, deadline, targets, expected_revision. Validate that retained capacities remain inside the new horizon; require availability replacement in a separate call before shortening the deadline if existing rows would fall outside it. Do not silently delete capacities. A fresh draft with both changes can instead be saved as a new goal.

PUT availability takes expected_revision plus availability array. Save normalized rows for all dates (missing=0), validate duplicate dates and horizon. Existing plan becomes stale after the revision changes.

## 4. Job contract

POST plan-jobs accepts expected_revision, mode=generate|replan, base_plan_id nullable. Generate requires no existing active plan. Replan requires the active plan ID. No client-created duration, reason, resource or assessment score is trusted.

Response includes job_id, status, accepted_revision, poll_url and request_id. A replay with the same idempotency key returns the same job_id. A different job while a student's job is active returns 409 JOB_IN_PROGRESS. At admission capacity return 429 JOB_CAPACITY with retry_after_seconds.

Transitions: queued → running → completed|failed. Startup recovery changes queued/running → interrupted. Terminal jobs are immutable; retry creates a new job. GET includes stage=accepted|snapshot|planning|retrieval|generation|validation|saving|done, result_plan_id or safe error. Do not provide invented progress percentages.

Failures: INPUT_INVALID, CURRICULUM_INVALID, STALE_INPUT, MODEL_UNAVAILABLE, INTERNAL_VALIDATION, JOB_INTERRUPTED. Partial feasibility is a completed planning outcome, not an HTTP failure. Model failure can produce a completed degraded plan with transparent template activities; the GenAI acceptance still needs a separate successful live-model run.

## 5. Plan response

Required top-level fields:

- plan_id, goal_id, version, parent_plan_id, input_revision, current_revision, is_stale.
- algorithm_version, policy_version, created_at, feasibility=full|partial|no_capacity.
- generation_status=generated|mixed|template_only; counts for each activity origin.
- metrics: capacity_minutes, remaining_work_minutes, scheduled_minutes, deferred_minutes, minute_shortfall, placement_conflict_count.
- entries: entry_id, work_item_id, topic_id, activity_kind, date, sequence, duration_minutes, activity, reason_code, reason_details.
- deferred: work_item_id, topic_id, remaining_minutes, reason_code.
- assumptions: estimated durations, evidence limitations, any template-only output.

Activity fields: title, steps (1–8 strings), expected_outcome, resource_ids, origin=generated|template|cache, model_id nullable, context_hash, validation_status. Duration comes only from scheduler; model cannot change it. Unknown resource references are invalid.

Completed history is returned separately from future entries. A saved plan is immutable. Current work status is an explicitly labeled overlay, not an overwrite of old plan content. The current-revision/stale fields may change because they describe the present state.

## 6. Progress and assessment

Progress payload: expected_revision, plan_id, work_item_id, event_type=completed|missed, actual_minutes optional 0–480. The referenced work item must belong to this goal and appear in the referenced plan. Only the active plan may accept a new event; clients refresh after a replaced version. Its is_stale flag alone does not block progress.

State transitions: pending → missed|completed; missed → missed|completed on a later scheduled occurrence; completed → completed is a no-op; completed → missed is 409 ALREADY_COMPLETED. Deduplicate the same occurrence via (work_item_id, plan_id, event_type). Corrections/reopening are deferred. actual_minutes is descriptive and never treated as fractional instructional completion.

Question responses expose question_id, skill_id, prompt, options, difficulty and form. Correct answers and explanations appear only after submission. GET selects unattempted reviewed items of the requested form; if none remain, return an empty list with question_pool_exhausted=true rather than silently repeat.

Attempt batch: expected_revision, items[{question_id, selected_option, hints_used}]. Maximum 10 items, no duplicate question IDs, option valid, hints_used integer 0–10. Grade on the server using reviewed keys. Return per-item result/explanation and evidence summary. hints_used is client-reported in the local prototype and must be labeled accordingly; it is not tamper-proof exam telemetry.

Every legitimate answer is logged, but only the first unhinted attempt on a question contributes independent evidence. Later answers on the same item are repetition, even if the earlier answer was wrong or hinted. No model grades core MCQ/code-trace items.

## 7. Error envelope

~~~json
{
  "error": {
    "code": "STALE_REVISION",
    "message": "Your progress changed. Refresh before updating the plan.",
    "details": {"current_revision": 4},
    "request_id": "request-example"
  }
}
~~~

Use 401 missing/invalid local token; 404 unknown/not-owned; 409 semantic conflict; 422 input validation; 429 bounded capacity; 503 process/database not ready. Model job failures are reflected in job state, not retroactively in the already-returned 202 response. Never expose tracebacks or provider secrets.

## 8. Internal interfaces

These names define responsibilities; actual type definitions are created during foundation:

~~~text
CurriculumService.get_snapshot(curriculum_id) -> CurriculumSnapshot
RetrievalService.retrieve(topic_id, objective, evidence, k=3) -> ResourceMatch[]
PlanningEngine.build(snapshot, policy) -> CandidatePlan
PlanningEngine.validate(candidate, snapshot) -> ValidationReport
ActivityService.enrich(task_contexts, budget) -> ActivityResult[]
ProgressService.record_event(command) -> ProgressReceipt
AssessmentService.score_batch(command) -> AttemptBatchResult
EvidenceService.project(student_id, skill_ids) -> SkillEvidence[]
PlanDiffService.compare(parent, candidate) -> PlanChange[]
ExportService.export(plan_snapshot, format) -> bytes
PlanningAgent.run(snapshot, policy) -> ValidatedPlanBundle
~~~

DTOs contain values, not live ORM sessions. Candidate generation does not write the database. The application service persists only after revision and validation checks.

## 9. Operational settings

Configuration names: DATABASE_URL, MODEL_BASE_URL, REASONING_MODEL, EMBEDDING_MODEL, EMBEDDING_FINGERPRINT, FRONTEND_ORIGIN, MODEL_TIMEOUT_SECONDS, MAX_ACTIVE_JOBS, APP_TIMEZONE, LOG_LEVEL. Secrets belong to environment configuration and never source control.

Default local policy: one worker; single inference permit; four admitted jobs maximum; 20-second provider read-inactivity timeout; one bounded repair attempt if generation output is invalid and budget remains. Soft whole-job generation budget is 45 seconds. HTTP read-inactivity timeout is not a hard wall-clock deadline; report true elapsed time and stop starting extra calls after the budget. Provider cancellation guarantees are not assumed.

Request logging includes request_id, route, status and elapsed_ms. Job logging adds stage, model fingerprint, validation failures, token counts if supplied, and fallback count. Avoid raw answers, full prompts, names and tokens in routine logs.
