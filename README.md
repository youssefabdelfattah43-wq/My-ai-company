# MY AI COMPANY
AI Business Operating System for SI NATURAL and an independent Paymob CRM workspace.

## Current status
This repository contains the initial architecture, agent permission registry, task handoff contract, and a Python task-routing MVP. It is not yet connected to WhatsApp, Meta Ads, Shopify, Canva, or a production AI model.

## Agent team
- Research
- Creative
- Media Buyer
- Sales & CRM
- Business Operations

## Run locally
Requires Python 3.10+.

```bash
python -m unittest discover -s tests
python -m src.orchestrator create --business si_natural --type content_creation --description "Draft three campaign concepts"
```

Sensitive actions (campaign publishing, budget changes, price changes, bulk messages, refunds, and external account changes) are created in `awaiting_approval` status.

## Repository layout
- `agents/agent-registry.json`: agent definitions and permissions
- `agents/agent-contract.json`: task and handoff contract
- `src/orchestrator.py`: task routing and approval gate MVP
- `tests/`: basic routing and approval tests
- `data/tasks/`: local task records (do not commit customer data)

## Security
- Never commit real API keys, tokens, passwords, customer records, or exports.
- Copy `.env.example` to `.env` locally and keep `.env` out of Git.
- Use official APIs and OAuth where available.
- Keep SI NATURAL and Paymob CRM data isolated.
- Require CEO approval before sensitive external actions.

## Next milestones
1. Validate the MVP locally.
2. Add persistent database storage and audit events.
3. Add model adapters and structured agent outputs.
4. Add n8n workflows and CEO approval dashboard.
5. Integrate external services one at a time, starting with read-only access.
6. Deploy to a suitable always-on host after confirming cost and account requirements.
