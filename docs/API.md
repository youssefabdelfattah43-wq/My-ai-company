# MY AI COMPANY API (MVP)

The API uses Python's standard library and SQLite. It is a development foundation, not a production deployment.

## Start

Set a long random token in the server environment (never commit it):
- `MYAI_API_TOKEN`
- Optional: `MYAI_HOST` (defaults to 127.0.0.1)
- Optional: `MYAI_PORT` (defaults to 8080)
- Optional: `MYAI_DATA_DIR` (defaults to data/runtime)

Run `python -m src.api`. Keep the service bound to localhost unless deployed behind HTTPS and a hardened reverse proxy.

## Authentication

All routes under `/api` require `Authorization: Bearer <MYAI_API_TOKEN>`. The health route exposes no business data. Never put the token in browser JavaScript, Git, screenshots or chat.

## Routes

- `GET /health`
- `GET /api/si_natural/tasks`
- `POST /api/si_natural/tasks`
- `GET /api/si_natural/approvals`
- `POST /api/si_natural/approvals/{task_id}/decision`
- Same routes under `/api/paymob_crm`

Task creation JSON: `{"task_type":"content_creation","description":"Draft a post"}`.
Sensitive action example: `{"task_type":"content_creation","description":"Prepare campaign","action":"campaign_publishing"}`. It is stored as awaiting CEO approval; this MVP does not publish ads or execute agent work.

Approval decision JSON: `{"decision":"approved","note":"Reviewed by CEO"}` or `{"decision":"rejected","note":"Needs changes"}`.

## Data isolation

Each business has a separate SQLite database file under its own directory. The API selects the database from a strict allowlist; the client cannot supply a filesystem path. Back up each business independently.

## Production gaps

Before internet exposure: add real user identity and role-based access, HTTPS, rate limiting, request logging, CSRF protections if cookie auth is added, secret management, backups, migrations, monitoring and deployment hardening. Do not connect real customer data until those controls are reviewed. The API token is a single shared MVP credential, not multi-user authentication.
