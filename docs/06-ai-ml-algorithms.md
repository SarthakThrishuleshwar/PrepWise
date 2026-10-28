# 06 — AI/ML concepts, methods and planning algorithms

## 1. What each method contributes

| Method | Actual purpose | Claim boundary |
|---|---|---|
| Prerequisite DAG | Logical ordering of curriculum-defined foundations | Not an AI-discovered universal concept graph |
| Priority-based constrained scheduling | Fit estimated activities into recorded daily capacity | Feasible heuristic; not globally optimal |
| Embedding retrieval | Find semantically relevant reviewed resources within allowed topics | Similarity is not truth, mastery or a dependency |
| Grounded language generation | Turn objectives/evidence/time into concrete activity instructions | Generated content needs validation |
| Rolling evidence estimate | Track recent independent performance by micro-skill | Not a calibrated probability of knowledge |
| Versioned replanning | Update remaining work after evidence/availability changes | A better plan does not prove long-term learning gain |

No base-model training, five-agent ensemble, reinforcement learning, or fine-tuning is necessary for the core. The adaptive property comes from persisted evidence changing future decisions. These methods are known; our contribution is a coherent implementation and evaluation.

## 2. Canonical planning snapshot

Inputs are immutable values: student timezone/input_revision; goal/horizon/target topics; per-date capacities; published curriculum hash and DAG; work items and events; skill projections; parent entries; algorithm and policy configuration.

Snapshot hash uses canonical JSON with sorted keys/IDs. Include semantically relevant data, not timestamps unrelated to decisions. Never use a live ORM object graph as a supposedly immutable snapshot.

Planning start is max(goal.start_date, local_today). Never place new work in the past. Deadline is inclusive. Capacity is the total study budget for a date, not an additional allowance every time the plan is regenerated.

For the current date subtract consumed study minutes from accepted completion events on that local date. Use max(original scheduled duration, reported actual_minutes when provided) per uniquely completed unit, capped at recorded capacity. An actual_minutes value of zero does not recover the full original allocation. This conservative rule prevents a replan from granting today's minutes twice. Missed units do not consume study minutes in MVP. Backdated activity and partial completion are deferred.

## 3. Goal closure and task graph

Let G=(V,E), where (u,v) means u must precede v. Validate DAG with Kahn's algorithm; time complexity O(V+E). Reject missing IDs, self edges, cycles and cross-curriculum edges.

Compute selected targets plus all ancestors using reverse traversal. Expose which foundations were included and why. Self-report alone does not remove a prerequisite.

Create stable work units from each topic's authored learn_minutes, practice_minutes and check_minutes. Published seed durations must be zero for optional absent stages or at least 5 minutes; learning is always at least 5. Split a stage into balanced units of at most 25 minutes: n=ceil(total/25); distribute quotient/remainder so totals are preserved. Example 55 → 19+18+18, not 25+25 plus an unusable 5-minute overflow decision made later. Keep unit keys stable across replans.

Within-topic order: learn units → practice units → check units. Dependent topic learning waits for the prerequisite's mandatory core units. Checks without reviewed questions are labeled self-check activities and do not update scored evidence. Optional review/remediation tasks have their own edges. Required units remain required even when deferred.

Completing a unit satisfies the scheduling edge, not proof of mastery. Separate assessment can insert repair work before remaining dependent tasks. Already-completed advanced work stays in history even if later evidence suggests a foundation needs repair.

## 4. Evidence projection

Use micro-skills with reviewed, single-skill questions. Every attempt is logged. Eligible evidence is only the first-ever attempt on that item, without hints. Hinted or repeated attempts are useful engagement history but excluded from independent scoring. Initial self-report is stored separately.

For each skill take the last W=8 eligible independent items in timestamp/ID order. Let c be correct, w incorrect, n=c+w:

~~~text
alpha = 1 + c
beta  = 1 + w
performance_estimate = alpha / (alpha + beta)
~~~

This is a smoothed recent item-success estimate. With n=0 return evidence_status=unknown rather than displaying 50% mastery. Rolling-window selection is our recency heuristic; this is not full Bayesian knowledge tracing or a stationary lifetime posterior. Different item difficulty remains a limitation; compare alternate items at similar authored difficulty.

Policy v1:

- Limited: fewer than 3 eligible items. Request another independent check; no strong diagnosis.
- Needs attention: n≥3 and estimate≤0.40. Add one bounded repair unit with a targeted check.
- Strong recent evidence: n≥4, estimate≥0.80, and at least one fresh followup-form item. Reduce unfinished practice units by at most 25%, minimum 5 minutes each. Do not skip all foundations or claim permanent mastery.
- Otherwise: preserve ordinary practice and gather evidence.

These thresholds are provisional product policies, not research-validated cutoffs. Store policy_version and constants on each plan. Projection is recomputable from attempts, so retries or service restarts must not increment alpha/beta again.

At topic level combine assessed skills conservatively: use the weakest sufficiently assessed skill for repair, not an average that hides a blocking gap. Unassessed skills remain unknown. No question bank coverage means no diagnosis claim.

## 5. Priority score and scheduling

Among ready tasks use normalized components:

~~~text
priority = .40 * weakness
         + .25 * goal_importance
         + .20 * prerequisite_leverage
         + .15 * review_urgency
~~~

weakness=1−estimate when enough evidence, neutral 0.5 otherwise. Optional low/high self-report adjusts unknown weakness by at most ±0.1, never overrides assessment. goal_importance comes from authored weights of reachable selected targets; foundations inherit the highest dependent target weight. prerequisite_leverage is number of target-relevant descendants divided by maximum relevant descendant count, or zero if none. review_urgency is 1 for an explicitly due review unit, zero otherwise. Constants are heuristics, not expected learning gain.

Tie-break by preserved valid parent placement, curriculum position, activity stage and stable ID. Priority does not override prerequisites or capacity.

~~~text
required = build_goal_closure_and_units(snapshot)
remaining = required minus completed_work_items
apply_bounded_evidence_adjustments(remaining)
for date in planning_dates:
    budget = available[date] - consumed[date]
    preserve feasible parent entries when predecessors and capacity allow
    while an unscheduled ready task fits the remaining budget:
        choose highest-priority fitting task, using stable tie-breaks
        place it; subtract its full duration; unlock successors
deferred = every remaining required unit not placed
validate(candidate)
~~~

Preservation is a heuristic, not an absolute lock: a newly inserted prerequisite repair or reduced availability can force moves. A ready task too large for the remainder is skipped for that date, not truncated. A five-minute remainder can hold a legitimate five-minute unit, not an invented “complete topic” task. A simple implementation scans ready tasks, giving approximately O(D*T²) worst case for D days and T units; sufficient for the bounded fixture.

MVP does not globally optimize learning gain. Exact optimization needs a defensible objective and calibrated estimates; add a solver later if a measured failure justifies it.

## 6. Feasibility and validation

C = sum effective remaining capacities; W = sum adjusted remaining required durations; S = sum scheduled durations; D = sum deferred durations.

Required conservation: W=S+D. minute_shortfall=max(0,W−C). C, W and S are nonnegative. Daily S_d≤C_d. Placement conflicts can exist even with minute_shortfall=0 because units are atomic and precedence restricts order.

Full iff D=0 and every constraint passes. Partial iff S>0 and D>0. No_capacity iff S=0 and D>0, including fragmented capacity smaller than any eligible activity. A fully completed goal has full feasibility, zero future entries, zero remaining work and a completed-goal message.

Validator rejects any candidate with unknown IDs, repeated unit, past/out-of-horizon date, nonpositive duration, overfilled date, unmet dependency, inconsistent totals, missing deferred unit, invalid resource reference or missing activity. Invalid candidate never becomes active. A valid partial candidate is not a validation failure.

Do not call topic coverage “mastery”. Scheduled coverage and assessed performance are separate metrics.

## 7. Retrieval design

Use reviewed resources with explicit topic IDs. Filter by curriculum and allowed topic/prerequisite before semantic ranking. Query combines objective, selected activity and concise supported evidence; exclude nickname/token. Chunk long resources by authored section, starting near 300 words with small overlap; record stable chunk/source IDs if chunking is introduced. MVP short resources are already retrieval units.

Encode documents and queries using the same model fingerprint and its required preprocessing. Reject vector dimension mismatch, nonfinite values, zero norm or stale content_hash. Normalize if the provider does not guarantee it. Cosine(q,d)=dot(q,d)/(norm(q)*norm(d)); use top k=3 within scope. Ties use resource ID. Small-corpus search is O(N*d), with cached document vectors.

Similarity is not probability. No universal score threshold is assumed; evaluate candidate relevance on the fixture. Prefer an exact topic-linked reviewed resource as deterministic fallback if embeddings fail or no eligible matches exist. If no resource exists, label missing source rather than invent a citation. Goal text may suggest candidate topics for confirmation; it cannot silently change targets.

## 8. Grounded generation contract

One planning agent constructs TaskContext objects containing work_item_id, objective, activity kind, fixed duration, concise evidence, allowed resource excerpts/IDs and output schema. Prompt says supplied content is data; instructions within it do not override the task. No arbitrary URLs, SQL, shell execution or autonomous web search tools.

Output must contain the same work_item_id, title, 1–8 actionable steps, expected_outcome, allowed resource_ids and brief rationale. Model cannot set time, grade, mastery, target scope or ownership. Do not request hidden chain-of-thought; ask for a short decision explanation.

Validate schema, ID coverage, allowed resource relationships, plausible activity scope and nonempty instructions. Schema compliance does not prove educational correctness. Seed review and relevance checks remain necessary.

Latency policy: build valid template activities for all units, then enrich up to the next six scheduled units in one bounded model batch. Label every origin. Later units retain concrete source-grounded template activities. A replan can enrich the next available batch. Maximum one output-repair request if time budget remains. Never call once per tiny unit without measuring latency.

Cache key includes task identity/objective, duration, evidence-policy state, resource hashes, model/prompt/policy versions and language. Different evidence or duration invalidates old instructions. Cached content remains labeled cache with its model provenance.

Fallback: use authored learn/practice/check instructions referencing real resources; label template. Generation_status is generated only if every entry was generated/cached with valid provenance; mixed if some templates; template_only if none generated. Cache is a provenance-preserving reuse, not a fresh call.

## 9. Adaptive decision process

Input event → revision update → new evidence projection → explicit replan → remaining-work estimate → valid task graph → schedule → grounded activities → explanation/diff.

- Missed work: keep required unit unfinished; prioritize carryover without completing it implicitly.
- Weak evidence: one stable repair unit per skill/policy cycle, default 10 minutes. Link it before unfinished dependent work. If no independent question remains, label limited assessment coverage.
- Strong evidence: bounded unfinished-practice reduction; no changes to completed units.
- New availability: recompute effective capacities; completed history survives.
- Due review: if last independent success was at least one local day earlier and no pending review exists, add one five-minute review unit for that assessed skill. This is an explicit scheduling heuristic; future review intervals remain an extension.

Do not infer a permanent misconception from one answer. A targeted follow-up may test a hypothesis; repeated matched errors support a more specific explanation. Do not assign visual/auditory learner labels or penalize slow answers.

## 10. Research extensions and honest claims

Bayesian Knowledge Tracing tracks latent skill state using learn/guess/slip assumptions [S08]. It can replace the estimator after item mapping and parameter evaluation exist. Contextual bandits need enough repeated intervention/outcome data and safeguards; merely choosing an explanation format is not evidence of reinforcement learning.

Retrieval practice has experimental support for retention [S09]. Our fixed review rule is a prototype policy, not a validated personalized forgetting model. Demonstrate fresh independent questions and distinguish immediate improvement from delayed retention or causal effect.
