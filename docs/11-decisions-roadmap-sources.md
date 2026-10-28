# 11 — Decisions, innovation roadmap and sources

## 1. Decision record

| Decision | Chosen direction | Reason / reconsider when |
|---|---|---|
| ADR01 | Student application fields, no upload dependency | User instruction; internal structured data still exists |
| ADR02 | Single planning agent | PS expectation; tools do not need autonomous identities |
| ADR03 | FastAPI modular monolith | Explicit backend preference, independent feature modules, low deployment overhead |
| ADR04 | SQLite now, relational services | Local-first execution; revisit on hosted concurrency |
| ADR05 | React/TypeScript/Vite and supplied design system | Owner supplied visual direction; see document 12 |
| ADR06 | Reviewed seeded curriculum | Makes grounding, prerequisites and assessment demonstrable |
| ADR07 | Heuristic scheduler + validator | Achievable and inspectable; solver later if measured benefit |
| ADR08 | Recent performance estimator first | Small data, clear assumptions; tracing model after evaluation |
| ADR09 | One inference configuration in shipped app | Reproducibility; developers can use their own model tools |
| ADR10 | Local in-process jobs with persisted status | Low setup; disclose interruption rather than claim durable execution |
| ADR11 | Source-grounded templates + bounded generated batch | Every task actionable without uncontrolled per-task latency |
| ADR12 | Stable work IDs + immutable versions | Progress survives plan changes and differences remain accurate |

The stack is selected for this team's constraints; no universal “best stack” or production-readiness claim is implied.

## 2. Innovations included with core

**Honest feasibility:** account for time and dependencies, preserve unresolved work, show concrete choices. Evidence: partial and fragmented-capacity fixtures.

**Evidence-driven adjustment:** independent answers and participation have different meanings; apply bounded changes with evidence counts. Evidence: different student histories produce different future allocations.

**Explainable recovery:** changes reference actual events; completed history survives. Evidence: before/after version comparison.

**Grounded provenance:** every activity refers to an allowed reviewed source and discloses generated/template/cache origin. Evidence: output inspection and unknown-ID rejection.

These are useful prototype differentiators rather than claims of new scientific inventions.

## 3. Expansion gates

| Later capability | Prerequisite evidence before adding | Evaluation |
|---|---|---|
| Targeted misconception diagnosis | Authored diagnostic item mapping and repeated evidence | Labeled error-pattern accuracy, abstention on ambiguity |
| Bayesian Knowledge Tracing | Valid skill mapping and enough sequences to assess parameters | Held-out calibration and predictive performance |
| Constraint-programming optimizer | Clear objective and heuristic baseline failures | Validity, runtime, objective improvement under same workload |
| Personalized review intervals | Delayed independent assessments across visits | Retention prediction and actual delayed performance |
| Learning which intervention helps | Repeated comparable intervention/outcome records | Evaluation avoiding selection bias; safe exploration plan |
| Arbitrary syllabus ingestion | Reliable extraction, author confirmation, graph validation | Mapping accuracy and invalid-content handling |
| Multi-user hosting | Authentication, access control, durable jobs and DB capacity | Security and concurrent consistency checks |

Do not add these before M0/M1 acceptance. An extra model call is not, by itself, an innovation.

## 4. Limitations and unresolved decisions

- Organizer's small metric acronym: verify source sheet.
- UI/UX is supplied and implemented as shared tokens/shell; feature owners follow document 12.
- Actual local model names/digests, context limits and hardware: benchmark during foundation.
- Exact dependency versions: lock one compatible installed set; families here are not claims of latest releases.
- Duration/priority/assessment thresholds: explicit provisional policy, need learner evaluation.
- Local token identity and in-process runner: event prototype scope, not a hosted production security/reliability model.

## 5. Verified primary references

Checked 28 October 2026. Sources establish capabilities/background; architecture choices, thresholds and schedules are our design. No long source extracts are reproduced.

- **S01:** [FastAPI relational database tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/) — database integration and request session pattern. Its example ORM choice does not require this project to use the same ORM wrapper.
- **S02:** [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/) and [async behavior](https://fastapi.tiangolo.com/async/) — after-response tasks and blocking/async integration.
- **S03:** [SQLAlchemy SQLite dialect](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html) — SQLite transaction, connection and foreign-key considerations.
- **S04:** [Ollama embeddings](https://docs.ollama.com/capabilities/embeddings) — embedding generation, cosine retrieval and consistent model use.
- **S05:** [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs) — JSON-schema output validation; verify support in the actual runtime/provider.
- **S06:** [Pydantic model concepts](https://docs.pydantic.dev/latest/concepts/models/) — typed model validation and schemas.
- **S07:** [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) — migration management.
- **S08:** [CMU knowledge-tracing walkthrough](https://www.cs.cmu.edu/~listen/BNT-SM/kt.html) — latent skill-state estimation from attempts. The MVP estimator is deliberately a different, simpler method.
- **S09:** [Roediger and Karpicke, 2006](https://pubmed.ncbi.nlm.nih.gov/16507066/) — experimental retrieval-practice evidence. Does not validate LearnNova's policy constants.
- **S10:** [OR-Tools precedence scheduling example](https://developers.google.com/optimization/scheduling/job_shop?hl=en) — constraint-based scheduling background, not a drop-in student planner.
- **S11:** [Sentence Transformers retrieve and rerank](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html) — semantic retrieval background. A cross-encoder reranker is not required for this small corpus.

## 6. Documentation change policy

Foundation owner updates contracts and this decision record together. Mark new functionality as designed, implemented or verified. Keep evaluation claims tied to recorded results. Frontend direction is now recorded in document 12; implemented foundation status is recorded in document 13.
