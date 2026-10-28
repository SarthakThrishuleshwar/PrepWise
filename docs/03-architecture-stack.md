# 03 — Application architecture and technology decisions

## 1. Architecture decision

Build a local modular monolith: one FastAPI backend process, one SQLite database, an in-process job runner, and a model gateway. The frontend is a React/TypeScript/Vite API consumer following document 12.

The planning agent is a bounded orchestrator with a fixed lifecycle. It uses validated functions and one selected reasoning model. It has no unrestricted autonomous tool loop and does not execute code produced by a model.

~~~mermaid
flowchart TD
    F[React / TypeScript / Vite] --> A[FastAPI /api/v1]
    A --> S[Application services]
    S --> D[(Local SQLite)]
    S --> J[Persisted jobs + in-process runner]
    J --> O[Single PlanningAgent]
    O --> P[Pure planning and validation]
    O --> R[Curriculum retrieval]
    O --> G[Model gateway]
    R --> V[Embedding cache in SQLite]
    G --> M[One reasoning model]
    R --> E[One embedding model]
~~~

## 2. Selected stack

| Layer | Choice | Rationale / constraint |
|---|---|---|
| Language | Python 3.10+; verified on 3.10.11 | Python 3.12 event target remains to verify; use one version team-wide |
| HTTP API | FastAPI with Uvicorn | Typed contract and generated OpenAPI; one local worker |
| Request/response validation | Pydantic 2 | Explicit DTOs; reject unknown fields on writes |
| ORM | SQLAlchemy 2.x | Explicit transactions and relational model; pick and lock one compatible tested release |
| Migrations | Alembic | One reviewed baseline migration; owner coordinates schema changes |
| Local DB | SQLite file, WAL | Minimal setup for one local demo; limited concurrent writes |
| Model client | HTTPX through owned gateway | Provider-specific details do not leak into features |
| Retrieval | NumPy cosine scoring over cached vectors | Sufficient for tens/hundreds of reviewed resources |
| Model runtime | Existing working local runtime, Ollama adapter if available | Actual model IDs selected by benchmark; no download dependency in demo |
| Tests | pytest + FastAPI test client | Meaningful acceptance and consistency checks |
| Frontend | React + TypeScript + Vite | Shared tokens/components following supplied UI/UX contract |

Version labels are compatibility families, not a claim they are the newest versions. Resolve/install and lock exact compatible versions once during foundation. Do not upgrade independently during the event. Current machine/runtime availability is not confirmed by this design.

## 3. Layer boundaries

Proposed application tree (to be implemented after documentation):

~~~text
backend/
  app/
    main.py
    core/          settings, logging, errors, identity context
    db/            engine, sessions, models, repositories
    contracts/     canonical public and internal DTOs
    api/v1/        thin routes, no scheduling logic
    features/
      curriculum/  seed, graph, resources, retrieval
      planning/    task builder, scheduler, validator, agent
      activities/  prompts, structured generation, fallbacks
      progress/    events, scoring, evidence projection
      insights/    plan diff, summary, export
    jobs/          acceptance, runner, state transitions
    providers/     reasoning and embedding adapters
  migrations/
  tests/
  data/            ignored local database and caches
~~~

Routes validate DTOs and call services. Services own transactions. Repositories persist/query. The planner accepts an immutable snapshot and returns a candidate; it does not access HTTP or mutate the database. The agent orchestrates these steps, not separate agent instances.

## 4. Runtime generation path

1. POST generation validates identity/goal and idempotency, persists queued job and snapshot revision.
2. Background runner opens its own session, atomically claims the job, reads a snapshot, then releases DB resources.
3. Planner computes target closure and work units, builds a schedule, validates it.
4. Retrieval selects only curriculum-compatible resources. Activity generation enriches selected units in a bounded batch.
5. Validator checks durations, IDs, topic/resource relationships and instructions; missing output receives labeled template fallback.
6. Final transaction compares current input_revision with the snapshot, checks candidate invariants, stores a new plan version and differences, and activates it.
7. Job completion returns the plan ID. Consumer polls job status then reads that plan.

On revision mismatch, fail with STALE_INPUT and keep the old plan. No partially written plan is activated. Inference must not keep write locks open.

## 5. Concurrency and jobs

Use synchronous SQLAlchemy sessions and ordinary synchronous FastAPI route functions for DB work; blocking model requests run in the background runner, not directly in async event-loop handlers. FastAPI supports background tasks after a response, but this is not a distributed durable queue [S02].

Prototype policy: one active generation/replan job per student, one model inference at a time, one Uvicorn worker, bounded admission (default four queued/running jobs total). Enforce student uniqueness in the DB and model concurrency in the gateway. Queue capacity check must be serialized under the local runner lock.

BackgroundTasks plus saved jobs gives observable state, not automatic crash recovery. On startup mark queued/running jobs from the previous process interrupted. Require an explicit retry with a new idempotency key. Never describe this as exactly-once execution or a production queue.

## 6. Local storage and deployment

Database path is configured relative to backend data directory, not current shell location. Set foreign_keys=ON on every SQLite connection, busy_timeout=5000, WAL once at initialization. Use short transactions. Do not share a SQLAlchemy Session between requests or worker threads [S03].

Bind backend and model runtime to loopback for the initial demo. Use configured frontend origin when selected. The local development identity is a generated client token whose hash maps to one student; routes derive identity, not trust a student ID supplied in the body. This is device-local prototype identity, not production authentication.

Migration path: keep services unchanged; move SQLite to PostgreSQL, background runner to durable worker, identity to real authentication, and vector search to an indexed service only when scale requires. These are future work, not preconditions for the hackathon.

## 7. Model selection and five developer machines

Each developer can develop with their available model and contract-compatible adapter. The final demonstration uses one known reasoning model and embedding configuration on one host. Compare valid structured-output rate, relevance, latency and memory on the same small fixture; choose the configuration that passes rather than the largest model name.

No requirement for network calls across five laptops. If the selected model is on a separate machine, validate connectivity and keep the endpoint configurable; do not make this the default architecture. Record provider, exact model identifier/digest when available, dimension, preprocessing and prompt versions.

Do not mix vectors from different models. A fingerprint covers model identity, normalization and query/document preprocessing; changes require reindexing [S04].

## 8. Sources

[S01–S10 and design tradeoffs](11-decisions-roadmap-sources.md) document official references. These sources support framework capabilities; the module structure and delivery policy are this project's design decisions.
