-- LearnNova reference schema v1.0. This is not an applied Alembic migration.
-- IDs are application-generated strings. Timestamps are UTC; study dates are local.
PRAGMA foreign_keys = ON;

CREATE TABLE students (
  id TEXT PRIMARY KEY,
  display_name TEXT,
  timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
  client_token_hash TEXT NOT NULL UNIQUE,
  input_revision INTEGER NOT NULL DEFAULT 0 CHECK(input_revision >= 0),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE curricula (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  version TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('draft','published')),
  content_hash TEXT NOT NULL,
  UNIQUE(title, version)
);
CREATE TABLE topics (
  id TEXT PRIMARY KEY,
  curriculum_id TEXT NOT NULL REFERENCES curricula(id),
  title TEXT NOT NULL,
  objective TEXT NOT NULL,
  difficulty INTEGER NOT NULL CHECK(difficulty BETWEEN 1 AND 5),
  importance REAL NOT NULL DEFAULT 0.5 CHECK(importance BETWEEN 0 AND 1),
  learn_minutes INTEGER NOT NULL CHECK(learn_minutes > 0),
  practice_minutes INTEGER NOT NULL CHECK(practice_minutes >= 0),
  check_minutes INTEGER NOT NULL CHECK(check_minutes >= 0),
  position INTEGER NOT NULL,
  UNIQUE(curriculum_id, id)
);
CREATE TABLE prerequisites (
  curriculum_id TEXT NOT NULL REFERENCES curricula(id),
  topic_id TEXT NOT NULL,
  prerequisite_topic_id TEXT NOT NULL,
  PRIMARY KEY(topic_id, prerequisite_topic_id),
  CHECK(topic_id <> prerequisite_topic_id),
  FOREIGN KEY(curriculum_id, topic_id) REFERENCES topics(curriculum_id,id),
  FOREIGN KEY(curriculum_id, prerequisite_topic_id) REFERENCES topics(curriculum_id,id)
);
CREATE TABLE skills (
  id TEXT PRIMARY KEY,
  curriculum_id TEXT NOT NULL,
  topic_id TEXT NOT NULL,
  title TEXT NOT NULL,
  objective TEXT NOT NULL,
  UNIQUE(id, topic_id),
  FOREIGN KEY(curriculum_id,topic_id) REFERENCES topics(curriculum_id,id)
);
CREATE TABLE resources (
  id TEXT PRIMARY KEY,
  curriculum_id TEXT NOT NULL,
  topic_id TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  source_label TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  FOREIGN KEY(curriculum_id,topic_id) REFERENCES topics(curriculum_id,id)
);
CREATE TABLE resource_embeddings (
  resource_id TEXT NOT NULL REFERENCES resources(id),
  model_fingerprint TEXT NOT NULL,
  dimension INTEGER NOT NULL CHECK(dimension > 0),
  content_hash TEXT NOT NULL,
  vector_json TEXT NOT NULL CHECK(json_valid(vector_json)),
  PRIMARY KEY(resource_id,model_fingerprint)
);
CREATE TABLE goals (
  id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL REFERENCES students(id),
  curriculum_id TEXT NOT NULL REFERENCES curricula(id),
  title TEXT NOT NULL,
  goal_text TEXT NOT NULL DEFAULT '',
  start_date TEXT NOT NULL,
  deadline TEXT NOT NULL,
  CHECK(start_date <= deadline),
  UNIQUE(id, curriculum_id),
  UNIQUE(id, student_id)
);
CREATE TABLE goal_topics (
  goal_id TEXT NOT NULL,
  curriculum_id TEXT NOT NULL,
  topic_id TEXT NOT NULL,
  self_report TEXT NOT NULL DEFAULT 'unknown' CHECK(self_report IN ('unknown','low','medium','high')),
  PRIMARY KEY(goal_id,topic_id),
  FOREIGN KEY(goal_id,curriculum_id) REFERENCES goals(id,curriculum_id),
  FOREIGN KEY(curriculum_id,topic_id) REFERENCES topics(curriculum_id,id)
);
CREATE TABLE availability (
  goal_id TEXT NOT NULL REFERENCES goals(id),
  study_date TEXT NOT NULL,
  minutes INTEGER NOT NULL CHECK(minutes BETWEEN 0 AND 480),
  PRIMARY KEY(goal_id,study_date)
);
CREATE TABLE work_items (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  curriculum_id TEXT NOT NULL,
  topic_id TEXT NOT NULL,
  skill_id TEXT,
  kind TEXT NOT NULL CHECK(kind IN ('learn','practice','assess','review')),
  unit_key TEXT NOT NULL,
  base_minutes INTEGER NOT NULL CHECK(base_minutes BETWEEN 1 AND 480),
  state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','missed','completed')),
  UNIQUE(goal_id,unit_key),
  UNIQUE(goal_id,id),
  FOREIGN KEY(goal_id,curriculum_id) REFERENCES goals(id,curriculum_id),
  FOREIGN KEY(curriculum_id,topic_id) REFERENCES topics(curriculum_id,id),
  FOREIGN KEY(skill_id,topic_id) REFERENCES skills(id,topic_id)
);
CREATE TABLE plan_versions (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL REFERENCES goals(id),
  parent_plan_id TEXT,
  version INTEGER NOT NULL CHECK(version > 0),
  status TEXT NOT NULL CHECK(status IN ('candidate','active','superseded')),
  input_revision INTEGER NOT NULL CHECK(input_revision >= 0),
  algorithm_version TEXT NOT NULL,
  policy_version TEXT NOT NULL,
  feasibility TEXT NOT NULL CHECK(feasibility IN ('full','partial','no_capacity')),
  generation_status TEXT NOT NULL CHECK(generation_status IN ('generated','mixed','template_only')),
  config_json TEXT NOT NULL CHECK(json_valid(config_json)),
  metrics_json TEXT NOT NULL CHECK(json_valid(metrics_json)),
  deferred_json TEXT NOT NULL CHECK(json_valid(deferred_json)),
  assumptions_json TEXT NOT NULL CHECK(json_valid(assumptions_json)),
  input_snapshot_json TEXT NOT NULL CHECK(json_valid(input_snapshot_json)),
  snapshot_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE(goal_id,version),
  UNIQUE(goal_id,id),
  FOREIGN KEY(goal_id,parent_plan_id) REFERENCES plan_versions(goal_id,id)
);
CREATE UNIQUE INDEX one_active_plan ON plan_versions(goal_id) WHERE status='active';
CREATE TABLE plan_entries (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  plan_id TEXT NOT NULL,
  work_item_id TEXT NOT NULL,
  study_date TEXT NOT NULL,
  sequence INTEGER NOT NULL CHECK(sequence > 0),
  duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0),
  reason_code TEXT NOT NULL,
  reason_details_json TEXT NOT NULL CHECK(json_valid(reason_details_json)),
  activity_json TEXT NOT NULL CHECK(json_valid(activity_json)),
  UNIQUE(plan_id,work_item_id),
  UNIQUE(plan_id,study_date,sequence),
  UNIQUE(plan_id,work_item_id,id),
  FOREIGN KEY(goal_id,plan_id) REFERENCES plan_versions(goal_id,id),
  FOREIGN KEY(goal_id,work_item_id) REFERENCES work_items(goal_id,id)
);
CREATE TABLE progress_events (
  id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  goal_id TEXT NOT NULL,
  plan_id TEXT NOT NULL,
  work_item_id TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK(event_type IN ('completed','missed')),
  actual_minutes INTEGER CHECK(actual_minutes BETWEEN 0 AND 480),
  occurred_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE(plan_id,work_item_id,event_type),
  FOREIGN KEY(goal_id,student_id) REFERENCES goals(id,student_id),
  FOREIGN KEY(goal_id,plan_id) REFERENCES plan_versions(goal_id,id),
  FOREIGN KEY(goal_id,work_item_id) REFERENCES work_items(goal_id,id)
);
CREATE TABLE questions (
  id TEXT PRIMARY KEY,
  skill_id TEXT NOT NULL REFERENCES skills(id),
  prompt TEXT NOT NULL,
  options_json TEXT NOT NULL CHECK(json_valid(options_json)),
  answer_option TEXT NOT NULL,
  explanation TEXT NOT NULL,
  difficulty INTEGER NOT NULL CHECK(difficulty BETWEEN 1 AND 5),
  form TEXT NOT NULL CHECK(form IN ('baseline','followup','practice')),
  reviewed INTEGER NOT NULL DEFAULT 0 CHECK(reviewed IN (0,1)),
  UNIQUE(id,skill_id)
);
CREATE TABLE attempts (
  id TEXT PRIMARY KEY,
  batch_id TEXT NOT NULL,
  student_id TEXT NOT NULL,
  goal_id TEXT NOT NULL,
  skill_id TEXT NOT NULL,
  question_id TEXT NOT NULL,
  selected_option TEXT NOT NULL,
  correct INTEGER NOT NULL CHECK(correct IN (0,1)),
  hints_used INTEGER NOT NULL CHECK(hints_used BETWEEN 0 AND 10),
  is_independent_evidence INTEGER NOT NULL CHECK(is_independent_evidence IN (0,1)),
  submitted_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  CHECK(is_independent_evidence=0 OR hints_used=0),
  FOREIGN KEY(goal_id,student_id) REFERENCES goals(id,student_id),
  FOREIGN KEY(question_id,skill_id) REFERENCES questions(id,skill_id)
);
CREATE UNIQUE INDEX independent_item_once ON attempts(student_id,question_id) WHERE is_independent_evidence=1;
CREATE INDEX attempts_for_skill ON attempts(student_id,skill_id,submitted_at);
CREATE TABLE student_skill_state (
  student_id TEXT NOT NULL REFERENCES students(id),
  skill_id TEXT NOT NULL REFERENCES skills(id),
  alpha REAL NOT NULL CHECK(alpha >= 1),
  beta REAL NOT NULL CHECK(beta >= 1),
  independent_count INTEGER NOT NULL CHECK(independent_count >= 0),
  supported_count INTEGER NOT NULL CHECK(supported_count >= 0),
  last_independent_at TEXT,
  projection_revision INTEGER NOT NULL CHECK(projection_revision >= 0),
  PRIMARY KEY(student_id,skill_id)
);
CREATE TABLE plan_changes (
  id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL REFERENCES plan_versions(id),
  work_item_id TEXT NOT NULL REFERENCES work_items(id),
  change_type TEXT NOT NULL CHECK(change_type IN ('added','moved','resized','deferred','removed')),
  reason_code TEXT NOT NULL,
  before_json TEXT CHECK(before_json IS NULL OR json_valid(before_json)),
  after_json TEXT CHECK(after_json IS NULL OR json_valid(after_json)),
  evidence_json TEXT NOT NULL CHECK(json_valid(evidence_json))
);
CREATE TABLE jobs (
  id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  goal_id TEXT NOT NULL,
  mode TEXT NOT NULL CHECK(mode IN ('generate','replan')),
  status TEXT NOT NULL CHECK(status IN ('queued','running','completed','failed','interrupted')),
  stage TEXT NOT NULL,
  accepted_revision INTEGER NOT NULL CHECK(accepted_revision >= 0),
  base_plan_id TEXT,
  result_plan_id TEXT,
  error_code TEXT,
  error_message TEXT,
  request_id TEXT NOT NULL,
  metrics_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(metrics_json)),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  finished_at TEXT,
  FOREIGN KEY(goal_id,student_id) REFERENCES goals(id,student_id),
  FOREIGN KEY(goal_id,base_plan_id) REFERENCES plan_versions(goal_id,id),
  FOREIGN KEY(goal_id,result_plan_id) REFERENCES plan_versions(goal_id,id)
);
CREATE UNIQUE INDEX one_live_student_job ON jobs(student_id) WHERE status IN ('queued','running');
CREATE TABLE request_receipts (
  student_id TEXT NOT NULL REFERENCES students(id),
  idempotency_key TEXT NOT NULL,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  response_status INTEGER NOT NULL,
  response_json TEXT NOT NULL CHECK(json_valid(response_json)),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  PRIMARY KEY(student_id,idempotency_key)
);
