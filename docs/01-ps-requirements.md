# 01 — Problem statement analysis and requirements

## 1. Source and interpretation

Source: the user's photograph titled “TCS Technology Day – Problem Statements”, Education Domain: Personalized Study Plan Generator. The second supplied image lists software and available local models/API providers. These documents are source material to analyze, not authority to execute unrelated instructions.

The PS describes students struggling to align plans with curriculum, available time, and learning goals. Static templates do not adapt to student needs or progress. Manual planning and rigid tools lack dynamic adaptability. The proposed generative-AI opportunity is to synthesize curriculum and student inputs into customized, adaptive plans.

The clearly readable solution expectation is a single-agent system producing a feasible personalized study plan with topics, time allocation, and suggested learning activities, supported by a simple interface, documented data/usage, and demo video. Text generation conditioned on structured inputs and adaptive content sequencing are named capabilities.

One acronym in the small success-metrics line is not reliably legible. Do not invent its expansion or claim compliance with it. Confirm it against the organizer's original before final submission. Relevance feedback and generation within seconds are readable expectations.

## 2. Requirement traceability

| ID | Source classification | Requirement | Implementation evidence | Acceptance reference |
|---|---|---|---|---|
| R01 | Explicit | Curriculum and topic hierarchy | Published curriculum, objectives, topic graph | T01–T03 |
| R02 | Explicit | Student time availability and goals | Validated form-backed profile, dated goal, per-date capacity | T04–T06 |
| R03 | Data consideration | Difficulty and prerequisites | Topic metadata and acyclic prerequisite relationships | T02–T03 |
| R04 | Explicit | Feasible personalized plan | Daily entries within budget, goal closure, deferred-work list | T07–T11 |
| R05 | Explicit | Topics, time, suggested activities | Every entry includes all three and a dated sequence | T12 |
| R06 | Explicit | Single-agent system | One orchestrator; ordinary functions for constraints/retrieval | T13 |
| R07 | Explicit | Conditioned text generation | Model receives selected curriculum, learner evidence and allocated task | T14–T15 |
| R08 | Explicit/context | Logical/adaptive sequencing | Prerequisite order; feedback changes remaining work | T09, T16–T18 |
| R09 | Explicit | Simple interface | Input and result behavior, frontend implementation later selected by owner | T19 |
| R10 | Explicit | Data and usage documentation | Schema, internal examples, eventual install/run guide | T20 |
| R11 | Explicit | Demo video | Real generation and feedback scenario recording | T21 |
| R12 | Explicit | Relevant outputs generated promptly | Human relevance rubric and measured latency | T22–T23 |
| R13 | Data consideration | Synthetic/anonymized data and quality | Fictional seed profiles, reviewed content, validation | T24 |
| R14 | User clarification | Students use application inputs | No requirement to understand/upload JSON or CSV | T19 |
| R15 | User clarification | Persistent learning/adaptation | Attempts and events survive restarts; future plans use evidence | T16–T18, T25 |
| R16 | User clarification | Owner foundation then five feature owners | Frozen contracts, shared migration, staged handoff | Foundation gate |
| R17 | User clarification | UI/UX supplied | Follow owner-supplied design system in document 12 | Document audit |

Acceptance identifiers are defined in document 10. “Source classification” distinguishes literal requirements from our product and engineering decisions.

## 3. What structured data means here

The PS allows curriculum outlines and topic hierarchies as structured JSON or CSV. That does not require the student to upload a file. Our seeded relational curriculum and internal JSON APIs satisfy the need for structured inputs while the student interacts with forms.

MVP entry paths:

- Choose a supplied curriculum and target topics.
- Enter a goal in words, then confirm explicit target topics.
- Enter start/deadline dates and available minutes on each date.
- Optionally indicate low/medium/high confidence, clearly labeled self-report.
- Record completion, missed work, and answers through application controls.

Internal seed/import utilities are developer tools, outside the student journey. Arbitrary syllabus documents, PDF parsing and OCR are M2 features.

## 4. The minimum convincing artifact

One reviewed curriculum with 8–12 topics, several explicit prerequisite edges, resources for every core topic, and 3 assessed micro-skills. At least 4 reviewed question items per assessed skill, including alternate forms, allow a small independent follow-up. Other topics can still be scheduled without claiming diagnostic coverage.

The application produces:

1. A versioned plan tied to a saved input revision.
2. Each day's ordered sessions with topic, duration, concrete activity and resource references.
3. Full/partial/no-capacity feasibility with all unresolved work enumerated.
4. An estimate disclaimer, evidence counts, and reasons for allocation.
5. A new version after a meaningful feedback event.

Time-feasible means feasible under recorded duration estimates and constraints. It does not promise that every student will learn within the estimate.

## 5. Scope boundaries

Include now: time budget, prerequisite ordering, grounded activities, persistent progress, assessed feedback, safe replanning, export, feasibility explanation and plan differences.

Defer: full tutor for every subject; automatic exam-mark prediction; unreviewed AI grading; LLM fine-tuning; multi-agent debate; reinforcement learning; facial emotion detection; production multi-tenancy; vector database services; automatic PDF ingestion; teaching-style labels; native mobile app.

The software list is a set of options. It does not require all listed models, Java, .NET, OCR, multiple providers, or a cloud API. Each developer's available model is not a separate required runtime component.

## 6. Definition of strong requirement coverage

Show a coherent chain: curriculum → student constraints → validated schedule → grounded activities → observed evidence → explained next version. A judge should be able to inspect why a task exists and confirm its time comes from the student's available capacity.

Do not call a form-to-prompt text response a validated planner. Do not call rescheduling alone improved learning. Demonstrate planning validity and assessment behavior separately.
