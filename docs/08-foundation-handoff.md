# 08 — Owner's foundation build and handoff

## 1. Ownership sequence

The project owner builds the common foundation before the five-person feature split begins. This is a shared platform task, not implementation of every feature. Once the foundation gate passes, the owner takes feature C (AI learning activities) and performs final integration after all feature handbacks. Four teammates take A/B/D/E; Member 3 owns planning (B). Document 09 defines file ownership and interface handoff rules for independent development.

Basic foundation is now implemented. Document 13 is the current execution/status handoff; this document records the design checklist and intended gate.

## 2. Freeze these decisions first

- Python version and one exact dependency lock, selected on the actual event machine.
- FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, SQLite; React/TypeScript/Vite and the supplied UI/UX contract.
- JSON DTO field names/enums; error envelope; local identity; revision/idempotency rules.
- One local reasoning-model adapter and one embedding adapter; model IDs confirmed by a real smoke call.
- One published reviewed curriculum and 3 assessed skills, represented internally as seed data.
- The supplied reference question items start reviewed=false. Check and approve their pedagogy/keys before serving them; a loader must not silently flip the flag.
- One Uvicorn worker; app-local job runner, explicit interrupted-job behavior.

Do not invent a model name from the photo. Query the installed runtime or test a configured endpoint. The supplied event environment says Python 3.12.8 is available; availability on this particular workspace has not been established by the design.

## 3. Foundation deliverables

| Deliverable | What owner implements | Ready check |
|---|---|---|
| Repository skeleton | Backend package and five feature directories | Imports resolve from documented project root |
| Dependency/environment setup | One virtual environment/lock, .env.example without secrets | All teammates can reproduce installation |
| Settings and logging | Configuration validation, request IDs, safe errors | Missing required setting fails clearly |
| DB integration | Engine/session factory, connection pragmas, baseline migration | Empty DB upgrades; FK checks active |
| Shared ORM models | Tables corresponding to reference schema | Constraints and indexes reproduced |
| Shared contracts | Input DTOs, PlanSnapshot, WorkItem, SkillEvidence, error/job enums | Fixtures parse; generated schema stable |
| Local identity | POST /students, token hash, GET /me, ownership dependency | Wrong token cannot read another goal |
| Job infrastructure | Accept/status/runner state helpers and recovery hook | A stub handler persists queued→completed/interrupted |
| Provider gateways | Typed reasoning/embed interfaces, real adapter and explicit fake test adapter | One structured response and vector batch verified |
| Seed command | Idempotent curriculum/resource/question insert | Running twice changes no existing progress |
| API registration | Routers import/register independently | OpenAPI builds with no circular imports |
| Test harness | Isolated temp DB and fake model fixture | No tests call a paid/slow model accidentally |

Stub feature endpoints should return 501 NOT_IMPLEMENTED with a feature code until their owner implements them. Never return successful fake plans as if the feature exists. Feature DTOs may be established before route behavior.

## 4. Foundation does not include

No full scheduler, final prompts, retrieval ranking, assessment policy, plan-diff logic or exports. The shared UI shell and working input flow are included after the owner supplied UI/UX direction. Those belong to feature owners. Shared models/contracts are the exception because independent conflicting schema designs block integration.

If time is tight, use the reviewed schema to produce the baseline migration directly, then implement thin repository methods per feature. Do not add a generic repository framework, dependency-injection container or agent framework solely for architectural appearance.

## 5. Suggested build order

1. Environment + settings + FastAPI health route.
2. SQLAlchemy session factory + baseline migration + seed loader.
3. Shared DTOs and error handlers; local identity dependency.
4. Provider interfaces + one real model check and deterministic fake test adapter.
5. Job infrastructure, revision helper and idempotency receipt helper.
6. Router wiring + smoke tests + handoff note.

Expected environment examples, once implementation exists:

~~~text
DATABASE_URL=sqlite:///./data/learnnova.db
MODEL_BASE_URL=http://127.0.0.1:11434
REASONING_MODEL=<verified-installed-model-id>
EMBEDDING_MODEL=<verified-installed-embedding-id>
APP_TIMEZONE=Asia/Kolkata
MAX_ACTIVE_JOBS=4
~~~

Relative DB URL must resolve from a documented backend working directory or be converted by settings to an absolute path. Frontend origin is configured after the owner chooses frontend execution details.

## 6. Foundation acceptance gate

All must be true before “start features”:

- [ ] GET /health and OpenAPI operate against a migrated local DB.
- [ ] Published sample curriculum can be seeded twice without duplicates.
- [ ] Identity and request ownership work; token secret never returned again.
- [ ] Shared request fixtures validate and invalid enums/IDs fail.
- [ ] Independent session per request/background task; no long inference transaction.
- [ ] Revision compare-and-increment and idempotent receipt transaction are reusable.
- [ ] Model gateway exposes real capability status; fake mode is explicitly labeled test-only.
- [ ] One saved job runs; restart interruption behavior is defined/tested.
- [ ] Each feature owner knows their files, routes, inputs, outputs and dependency contacts.
- [ ] Database migration/contracts are frozen for the first feature pass.

The gate tests actual backend foundation; checking the supplied reference SQL alone does not satisfy it.

## 7. Handoff message template

Share repository revision, setup/run commands, environment names, model identifiers, DB migration command, seed command, passing foundation checks, frozen DTO location, feature directory map and known limitations. Include a sample local token only through the running local app, never committed in documentation.

Teammates can read documentation and review curriculum while foundation is being built. They start feature implementation after the owner gives this handoff. Schema changes afterward are proposed to the owner, not independently applied.

## 8. Time management

Two-hour target allocation: roughly 35 minutes foundation, 55 minutes concurrent feature work, 20 minutes integration/acceptance, 10 minutes demo preparation. This is an execution target, not a completion guarantee. Use gates to assess scope honestly.

If a gate fails, fix the blocking contract/runtime issue first. Cut advanced retrieval tuning, extra visuals, multiple subjects or rich tutoring before cutting valid scheduling, persistence, one live grounded-generation path or the required submission documents/video.
