# Reference validation record

Checked 28 October 2026 with the workspace Python 3.10 runtime and SQLite 3.40.1. The implementation target remains Python 3.12.x; application/runtime compatibility on that target must be checked during foundation.

Command from repository root:

~~~text
python docs/reference/validate_reference.py
~~~

Validated scope:

- Local Markdown links and balanced fenced blocks.
- Five JSON reference files parse; goal request passes its Draft 2020-12 JSON Schema with format checking.
- Reference SQL initializes 20 tables in memory with foreign keys enabled.
- Selected negative cases reject invalid availability, missing/self prerequisites, duplicate live student jobs and duplicate active goal plans.
- Seed has eight topics, an acyclic graph, three assessed-skill definitions and 18 draft question keys whose calculations agree with independent reference calculations.
- Reference full plan accounts for 105 minutes within 420 available minutes, respects prerequisites, references valid resources and correctly identifies template provenance.

Questions deliberately remain reviewed=false pending team approval. Computed key consistency does not replace educational/content review.

Not validated: FastAPI application, ORM mappings, Alembic migration, live model behavior, real learner outcomes, latency, frontend, or UI/UX. Those are implementation acceptance work in document 10. These reference checks do not cover the implemented foundation; see document 13 and backend/frontend test suites for current status.
