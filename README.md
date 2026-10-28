# LearnNova

A curriculum-grounded personalized study planner. **Basic foundation implemented; feature owners can start.**

Start with [setup and handoff](docs/13-foundation-status-runbook.md), [five-person split](docs/09-team-feature-split.md), and [the UI/UX contract](docs/12-ui-ux-design-system.md).

## Ready

FastAPI API, local SQLite/Alembic migration, 20 SQLAlchemy table models, identity, saved goals and availability, typed shared contracts, job lifecycle, model adapters, seed curriculum and React/TypeScript/Vite shell. Student inputs are application forms. Fonts are bundled locally.

## Feature work remaining

Planning/agent logic, semantic retrieval, generated activities, progress/assessment and comparison/export are assigned to five feature owners. Their unimplemented API seams return explicit 501 errors. No fake plans or learning scores are presented. Real model IDs must be configured on the event machine; model adapters have mocked contract tests.

## Start development

See [the runbook](docs/13-foundation-status-runbook.md) for backend installation, migrations, seed and server commands, plus frontend setup and checks. Backend uses Python 3.10+ (verified here on 3.10.11); frontend verified with Node 24.11.0. Use the checked-in dependency locks.

## Five feature areas

| Member | Feature | Working folders under backend/app/features and frontend/src/features |
|---|---|---|
| You / Member 1 | AI activities and final integration | activities |
| Member 2 | Curriculum and retrieval | curriculum |
| Member 3 | Personalized planning | planning |
| Member 4 | Progress and assessment | progress |
| Member 5 | Explanations and export | insights |

All feature UI follows the supplied design system: near-white surfaces, electric blue, Host Grotesk, Instrument Sans, visible focus and reduced-motion support. Shared contracts/components/migrations stay owner-controlled.

Full product and technical specifications: [documentation index](docs/README.md).
