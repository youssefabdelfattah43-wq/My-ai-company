"""SQLite persistence with strict per-business database separation."""
from __future__ import annotations
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("MYAI_DATA_DIR", ROOT / "data" / "runtime"))
BUSINESSES = {"si_natural", "paymob_crm"}

def db_path(business: str) -> Path:
    if business not in BUSINESSES:
        raise ValueError("Unknown business workspace")
    folder = DATA_ROOT / business
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "company.sqlite3"

def connect(business: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path(business))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize(business: str) -> None:
    with connect(business) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
          id TEXT PRIMARY KEY, business TEXT NOT NULL, task_type TEXT NOT NULL,
          description TEXT NOT NULL, assigned_agent TEXT NOT NULL, action TEXT,
          status TEXT NOT NULL, approval_required INTEGER NOT NULL,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL, result_json TEXT
        );
        CREATE TABLE IF NOT EXISTS approvals (
          id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL UNIQUE,
          action TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
          requested_at TEXT NOT NULL, decided_at TEXT, decision_note TEXT,
          FOREIGN KEY(task_id) REFERENCES tasks(id)
        );
        CREATE TABLE IF NOT EXISTS audit_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL,
          task_id TEXT, details_json TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
        """)

def save_task(task: dict[str, Any]) -> None:
    business = task["business"]
    initialize(business)
    with connect(business) as db:
        db.execute("""INSERT INTO tasks
          (id,business,task_type,description,assigned_agent,action,status,
           approval_required,created_at,updated_at,result_json)
          VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
          (task["id"],business,task["task_type"],task["description"],
           task["assigned_agent"],task.get("action"),task["status"],
           int(task["approval_required"]),task["created_at"],task["updated_at"],
           json.dumps(task.get("result"), ensure_ascii=False)))
        if task["approval_required"]:
            db.execute("""INSERT INTO approvals(task_id,action,requested_at)
                          VALUES(?,?,?)""",
                       (task["id"],task["action"],task["created_at"]))
        db.execute("INSERT INTO audit_events(event_type,task_id,details_json,created_at) VALUES(?,?,?,?)",
                   ("task_created",task["id"],json.dumps({"task_type":task["task_type"]}),task["created_at"]))

def list_tasks(business: str, status: str | None = None) -> list[dict[str, Any]]:
    initialize(business)
    with connect(business) as db:
        rows = db.execute("SELECT * FROM tasks WHERE status=? ORDER BY created_at DESC", (status,)).fetchall() if status else db.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]

def list_approvals(business: str) -> list[dict[str, Any]]:
    initialize(business)
    with connect(business) as db:
        rows = db.execute("""SELECT a.*,t.task_type,t.description,t.assigned_agent
          FROM approvals a JOIN tasks t ON t.id=a.task_id
          WHERE a.status='pending' ORDER BY a.requested_at DESC""").fetchall()
    return [dict(row) for row in rows]

def decide_approval(business: str, task_id: str, decision: str, note: str = "") -> bool:
    if decision not in {"approved", "rejected"}:
        raise ValueError("Decision must be approved or rejected")
    initialize(business)
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    with connect(business) as db:
        row = db.execute("SELECT status FROM approvals WHERE task_id=?", (task_id,)).fetchone()
        if row is None or row["status"] != "pending":
            return False
        db.execute("UPDATE approvals SET status=?,decided_at=?,decision_note=? WHERE task_id=?",
                   (decision,now,note[:500],task_id))
        db.execute("UPDATE tasks SET status=?,updated_at=? WHERE id=?",
                   (decision,now,task_id))
        db.execute("INSERT INTO audit_events(event_type,task_id,details_json,created_at) VALUES(?,?,?,?)",
                   ("approval_"+decision,task_id,json.dumps({"note":note[:500]}),now))
    return True
