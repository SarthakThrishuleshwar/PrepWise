# 07 — Application and service workflows

These workflows define behavior and data transitions. Screen layout, visual states, component selection and frontend framework are pending the owner's UI/UX direction.

## 1. Local onboarding and goal setup

1. Application obtains local identity from POST /students and retains the returned token.
2. Read published curricula; student selects one and explicit target topics.
3. Student enters dates, availability and optional goal text/confidence in normal fields.
4. Application expands any convenience availability pattern into dated rows. No file upload.
5. POST /goals validates all relationships and saves revision 1.
6. Student can review normalized values. Unknown confidence stays unknown.

If goal text suggests another topic, retrieval can offer a candidate, but only explicit student confirmation changes targets. Missing dates become zero. Invalid dates/edges return a specific explanation; they never become a guessed plan.

## 2. Initial generation sequence

~~~mermaid
sequenceDiagram
    participant C as Application consumer
    participant API as FastAPI
    participant DB as SQLite
    participant Agent as PlanningAgent
    participant Model as Model gateway
    C->>API: POST plan-jobs + revision + idempotency key
    API->>DB: Save queued job and receipt
    API-->>C: 202 job_id
    API->>Agent: Background task with job_id
    Agent->>DB: Claim job; load snapshot; close session
    Agent->>Agent: Build required work, schedule, validate
    Agent->>Model: Grounded activity batch
    Model-->>Agent: Structured activities or bounded failure
    Agent->>Agent: Validate / label template fallback
    Agent->>DB: Check revision; atomically save and activate
    C->>API: GET job
    API-->>C: completed + plan_id
    C->>API: GET plan
    API-->>C: Entries, deferred work, origins, assumptions
~~~

The generation job is observable, but background execution is not durable across process failure. A job is completed only after a valid version is committed.

## 3. Studying and completion

Student uses a scheduled activity and its reviewed resource. Completion request references active plan and stable work item. The service records a single occurrence, marks the work item completed, increments input_revision and returns is_plan_stale=true.

Completion measures reported participation. It does not automatically increase assessed skill score. If the student completes ahead of the scheduled date, the server's current local date determines consumed capacity for replanning. Backdated completion entry is not in MVP.

Completing an already-completed unit is a no-op. Retrying the same idempotency key returns the original result. Marking completed work missed is rejected. The previous plan still shows what was originally scheduled; current status is an overlay.

## 4. Assessment and targeted support

1. Retrieve fresh reviewed questions for an assessed skill.
2. Return prompt/options without answer keys.
3. Student submits a batch; application supplies observed/self-reported hint count as documented.
4. Server scores using reviewed keys, stores answers, explains the correct result.
5. Only first-ever unhinted item attempts contribute independent evidence.
6. Recompute the rolling estimate and evidence count in the same transaction.
7. Return recommended next action: more evidence, ordinary practice, bounded repair or increased challenge.
8. Student explicitly requests plan update; the job uses the new revision.

Wrong answer → hypothesis, not diagnosis. A fresh follow-up can investigate a suspected range-boundary or accumulator error. If the bank is exhausted, acknowledge insufficient independent items; do not manufacture proof of improvement from repeats.

## 5. Replanning after missed work

Student marks a scheduled unit missed. It remains required and unfinished. Replan takes active plan as parent, removes completed units from future work, subtracts today's consumed time, and places remaining work within current capacity.

Preserve valid unchanged future placements when possible. Move necessary dependents after the missed foundation. Record MISSED_WORK or PREREQUISITE reason codes with real event IDs. A missed advanced unit does not automatically force repeating every foundation.

## 6. Availability and goal changes

PUT availability replaces the normalized map and increments revision. PATCH goal changes explicit target scope or horizon under validation. Existing active plan becomes stale but readable.

Replan computes current capacity and remaining effort. It does not silently extend the deadline. If the result is partial, list every deferred unit and explain whether total time or placement/ordering caused the shortfall. Student may explicitly increase capacity, change deadline or target scope and request another version.

Removed target work that is still needed as a prerequisite remains required. Completed work for a removed target remains history. It is never recreated as pending to fit the new plan.

## 7. Plan-version comparison

Compare stable work IDs across parent/new entries:

- added: newly required task such as a repair.
- moved: date or within-day sequence changed.
- resized: estimated duration changed by a bounded evidence policy.
- deferred: previously scheduled required unit no longer fits.
- removed: no longer required by explicit scope or completed before new plan.

For each, include structured before/after values and deterministic reason/evidence. Unchanged units need no change row; include unchanged_count in summary. “Removed because completed” is not “deferred”. Old content snapshots remain readable.

Use established codes INITIAL_GOAL, PREREQUISITE, SELF_REPORT, LOW_EVIDENCE, PRACTICE_REPAIR, INDEPENDENT_SUCCESS, MISSED_WORK, AVAILABILITY_CHANGED, REVIEW_DUE, CAPACITY_LIMIT, FRAGMENTED_CAPACITY, USER_SCOPE_CHANGED, COMPLETED_WORK. The server assigns codes; generated prose may explain them but cannot invent events.

## 8. Failure and race handling

| Situation | Behavior |
|---|---|
| Student answers while generation runs | Input revision advances; stale job cannot activate |
| Double-click generate | Same key replays; different key while active gets JOB_IN_PROGRESS |
| Model unavailable | Valid template activities, explicit provenance; preserve all progress |
| Embedding unavailable | Exact topic-linked source lookup, retrieval degradation recorded |
| Invalid generated resource ID | Reject affected output, use valid template |
| Invalid curriculum DAG | Stop generation; do not try to repair graph using guesses |
| App restarts mid-job | Mark interrupted; allow explicit retry; previous plan survives |
| Empty effective availability | Completed no_capacity result with unresolved work |
| Entire goal completed | Full result, no future entries, completed-goal explanation |

## 9. Export and resumption

Exports are tied to plan_id/version, not a floating current-plan query. JSON includes entries, assumptions and deferred work; CSV includes version/date/sequence/topic/kind/duration/instructions/origin/reason and a separate row_type for deferred items. Quote cells properly and neutralize spreadsheet formula prefixes in free-text cells.

On resumption read /me, saved goal, current plan and learning state. Do not reset seed or progress at startup. A stale plan must disclose that newer inputs exist. No notification, calendar sync or background automated study nudging is implied.
