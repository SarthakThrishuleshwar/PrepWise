# Internal contract examples

These are developer/API examples, not student-upload requirements. Students supply ordinary application fields. The application serializes requests internally.

- goal-create.json: example saved goal request with seven dated capacities.
- attempt-batch.json: example answer submission, not an answer key.
- curriculum-seed.json: synthetic curriculum and 18 draft assessment items for a future developer seed loader; questions remain reviewed=false until the team approves them.
- plan-example.json: complete example full plan for a loops goal with no prior progress; all activities are honestly labeled templates.
- goal-create.schema.json: machine-readable request shape; semantic date/graph/ownership checks remain application logic.

Freeze local_today=2026-10-28 when validating these date-specific examples. Live demo setup should generate dates relative to its actual local date. Seed readable IDs are stable authoring identifiers; API-created IDs are opaque generated strings.

The reference SQL schema and these examples are checked separately from the future ORM/API. No application service is present yet. The plan example illustrates data semantics, not a live generated result or a measured learner improvement.

Run the standard-library reference check from the repository root:

~~~text
python docs/reference/validate_reference.py
~~~

It checks local documentation links, SQL initialization and selected constraints, seed relationships, answer-key calculations, and plan accounting. If jsonschema is installed it also validates the goal against the supplied JSON Schema; otherwise that optional check is explicitly skipped. This does not test an application that has not been built.
