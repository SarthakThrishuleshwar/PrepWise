# 10 — Evaluation, acceptance and submission

## 1. Evaluation principles

Measure validity, relevance, adaptation and observed performance separately. A well-formatted answer can still be an invalid plan. A higher internal estimate can occur without demonstrated transfer or retention. Report real measurements, not aspirational numbers.

The following checks are an implementation acceptance plan. They have not been run against an application because application code is not part of this documentation deliverable.

## 2. Acceptance matrix

| ID | Setup/action | Expected evidence |
|---|---|---|
| T01 | Seed curriculum twice | Same published content, no duplicates or progress reset |
| T02 | Introduce missing/cross-curriculum prerequisite | Rejected before publication/generation |
| T03 | Introduce graph cycle | Clear curriculum error, no active invalid plan |
| T04 | Submit invalid dates/capacity | 422 field-specific response |
| T05 | Omit date from availability | It receives zero capacity |
| T06 | Select advanced target | Required ancestor closure explicit |
| T07 | Generate full-capacity fixture | Daily minutes within effective capacity |
| T08 | Set all capacities zero | no_capacity, no sessions, complete deferred list |
| T09 | Inspect topic/work graph | Every prerequisite unit precedes its successor |
| T10 | Give insufficient total minutes | partial result, honest shortfall/deferred work |
| T11 | Give fragmented capacity | Placement conflict identified even when total capacity suffices |
| T12 | Inspect every entry | Topic, time, activity, source and reason present |
| T13 | Review runtime architecture | One planning agent, model/embedding functions are tools |
| T14 | Live model generation | Valid grounded activities and actual provider/model provenance |
| T15 | Inject unknown resource ID or timeout | Output rejected; labeled fallback; valid schedule remains |
| T16 | Complete a session, restart | Event persists; future plan does not repeat completed work |
| T17 | Mark foundation missed then replan | Unfinished foundation moved; dependent future work respects order |
| T18 | Submit independent assessment | Projection changes; bounded policy affects remaining work |
| T19 | Complete journey using application fields | No CSV/JSON upload knowledge required |
| T20 | Follow setup/data guide | Reproducible environment, seed, run and sample input documented |
| T21 | Record demonstration | Real end-to-end flow; synthetic scenarios explicitly labeled |
| T22 | Time cold/warm runs | Actual latency, hardware/model and sample count recorded |
| T23 | Review generated activities | Human rubric scores relevance/actionability; failures retained |
| T24 | Review seed/content | Fictional profiles, correct reviewed answer keys and source text |
| T25 | Reload plan history | Versions and input revisions remain consistent |
| T26 | Replay same idempotency key | Same response, no duplicate job/event/attempt |
| T27 | Change payload with same key | 409 idempotency conflict |
| T28 | Mutate evidence during generation | STALE_INPUT job; previous active plan retained |
| T29 | Replan after today's completed work | Used minutes subtracted once, no daily capacity inflation |
| T30 | Change student token | Other student's resources unavailable |
| T31 | Retry seen/hinted question | No independent evidence inflation |
| T32 | Interrupt process mid-job | Terminal interrupted status after restart; explicit retry |
| T33 | Export text with commas/formula prefix | Valid escaped CSV; formula activation neutralized |
| T34 | Remove selected target | Required closure recalculated; completed history preserved |
| T35 | Finish every required unit | Full, empty future schedule, completed-goal explanation |

Automate deterministic core invariants and consistency/race checks. Use manual review for semantic educational relevance and actual consumer interaction. No need for tests that merely repeat a trivial getter implementation.

## 3. Test strategy

Pure planner tests: isolate date clock and policy, no DB/model. Include DAG, zero-capacity, fragmentation, completion, deterministic tie breaks and minute conservation. A small randomized DAG/capacity check can test conservation and precedence across many cases without asserting one exact layout.

Database/API tests: temp file SQLite, real FK/unique constraints, FastAPI test client, fake provider, independent sessions. Test idempotency, stale revision and final activation rollback. File-backed DB better approximates local connection behavior than accidentally isolated in-memory connections.

Provider smoke test: opt-in, explicit real endpoint, small fixed batch. Record model, output validity, relevance and elapsed time. Do not make every test call a live model.

Question validation: human checks each answer key; code-trace questions may be independently verified against known program outputs in a controlled test. Never execute arbitrary student/model code as the grading method.

## 4. Metrics and denominators

- Constraint violation rate: invalid schedules / generated candidates. Release target: zero activated invalid plans.
- Required work accounting: scheduled + deferred = remaining required minutes on every saved version.
- Independent performance: correct / eligible fresh attempts, reported with item count and form/difficulty.
- Relevance rubric: score each activity 0–2 for objective match, source consistency, actionable steps and scope appropriate to time; retain per-item review.
- Adaptation correctness: meaningful event scenarios producing the expected bounded policy / scenarios checked.
- Stability: unchanged still-feasible work retained / parent work eligible for retention. No fabricated target until measured.
- Provenance coverage: entries with valid resources / all entries; generated/template/cache counts separately.
- Latency: record individual times. With at least 20 samples report median and p95; with fewer, report sample count and range instead of an impressive-looking percentile.

BLEU/ROUGE-like text overlap, if required by the unclear source acronym, would be supplemental and need a proper reference text. It cannot replace validity or relevance. This is a conditional note, not a transcription of the PS.

## 5. Canonical demonstration fixtures

Use the documented curriculum and freeze local_today=2026-10-28 for automated examples; recreate dates relative to demo day for live use.

1. Time-rich novice: low self-report, no assessment; normal foundations and practice, unknown evidence label.
2. Strong recent evidence: at least four independent comparable items including fresh followup; bounded practice reduction.
3. Weak evidence: at least three independent items, low estimate; one repair unit and appropriate dependency.
4. Disruption: completed work plus missed foundation; future-only repair with consumed-capacity accounting.
5. Impossible scope: workload exceeds capacity; visible deferred units and options.

The reference seed has multiple forms. A simulated response sequence proves system behavior, not a real learner outcome. If a real participant attempts baseline and followup, show their actual answers and disclose the small sample.

## 6. Three-minute video outline

0:00–0:20: State problem and student goal; show supplied curriculum.

0:20–0:55: Enter availability through ordinary application fields; generate plan; show measured duration and one grounded activity.

0:55–1:25: Explain capacity and prerequisite evidence; complete or miss one session.

1:25–2:05: Submit a reviewed assessment; show evidence count and next-action reason; trigger update.

2:05–2:35: Compare versions, explain changed/unchanged sessions and deferred work if capacity was reduced.

2:35–3:00: Show persisted history/export and briefly state limits. UI/UX execution will follow owner's separate direction.

If the model is unavailable during filming, use a clearly labeled saved run for illustration and separately capture a successful live path when possible. Do not silently relabel prerecorded/template content as live AI.

## 7. Submission checklist

- Working source and exact dependency lock.
- Final run guide verified on the actual machine.
- Sample curriculum, internal data format, reviewed question bank.
- Model identifiers/runtime prerequisites without committed secrets.
- Architecture, algorithm policy, database and API documentation.
- Measured acceptance results and relevance feedback.
- Demo video and a short explanation of problem coverage/innovations.
- Known limitations: local identity, local job recovery, estimated durations, limited assessment coverage.
- Verify any unreadable organizer metric from original handout.
