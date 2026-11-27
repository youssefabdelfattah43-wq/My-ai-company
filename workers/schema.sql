CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  business TEXT NOT NULL CHECK (business = 'si_natural'),
  task_type TEXT NOT NULL,
  description TEXT NOT NULL,
  assigned_agent TEXT NOT NULL,
  status TEXT NOT NULL,
  approval_required INTEGER NOT NULL DEFAULT 0,
  action TEXT,
  result TEXT,
  error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
  id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL UNIQUE REFERENCES tasks(id),
  action TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  requested_at TEXT NOT NULL,
  decided_at TEXT,
  decision_note TEXT
);
CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  task_id TEXT,
  details TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_si_tasks_created ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_si_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_si_approvals_status ON approvals(status);
CREATE TABLE IF NOT EXISTS public_task_usage (id TEXT PRIMARY KEY, ip_hash TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_public_usage_ip_created ON public_task_usage(ip_hash, created_at);
