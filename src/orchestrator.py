"""MY AI COMPANY task orchestrator MVP.

This module routes tasks to registered agents and enforces human approval
for sensitive actions. It deliberately does not call external services yet.
Run: python -m src.orchestrator --help
"""
from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "agents" / "agent-registry.json"
TASKS_DIR = ROOT / "data" / "tasks"
APPROVAL_ACTIONS = {
    "campaign_publishing", "budget_changes", "price_changes",
    "bulk_messages", "refunds", "external_account_changes",
}
AGENT_BY_TASK = {
    "research": "research",
    "competitor_analysis": "research",
    "content_creation": "creative",
    "ad_copywriting": "creative",
    "campaign_analysis": "media_buyer",
    "read_ad_reports": "media_buyer",
    "lead_followup": "sales_crm",
    "manage_leads": "sales_crm",
    "order_report": "operations",
    "inventory_report": "operations",
    "profit_report": "operations",
}

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_registry() -> dict[str, Any]:
    with REGISTRY_PATH.open(encoding="utf-8") as f:
        return json.load(f)

def route_task(task_type: str) -> str:
    try:
        return AGENT_BY_TASK[task_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported task_type: {task_type}") from exc

def requires_approval(action: str | None) -> bool:
    return action in APPROVAL_ACTIONS

def create_task(business: str, task_type: str, description: str,
                action: str | None = None) -> dict[str, Any]:
    registry = load_registry()
    if business not in registry["businesses"]:
        raise ValueError(f"Unknown business environment: {business}")
    agent_id = route_task(task_type)
    allowed = {agent["id"] for agent in registry["agents"]}
    if agent_id not in allowed:
        raise ValueError(f"Agent is not registered: {agent_id}")

    task = {
        "id": str(uuid.uuid4()),
        "business": business,
        "task_type": task_type,
        "description": description,
        "assigned_agent": agent_id,
        "action": action,
        "status": "awaiting_approval" if requires_approval(action) else "queued",
        "approval_required": requires_approval(action),
        "created_at": now(),
        "updated_at": now(),
        "handoffs": [],
        "result": None,
    }
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    path = TASKS_DIR / f"{task['id']}.json"
    path.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
    return task

def main() -> None:
    parser = argparse.ArgumentParser(description="MY AI COMPANY task router MVP")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create", help="Create and route a task")
    create.add_argument("--business", required=True, choices=["si_natural", "paymob_crm"])
    create.add_argument("--type", required=True, choices=sorted(AGENT_BY_TASK))
    create.add_argument("--description", required=True)
    create.add_argument("--action", choices=sorted(APPROVAL_ACTIONS))
    args = parser.parse_args()
    task = create_task(args.business, args.type, args.description, args.action)
    print(json.dumps(task, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
