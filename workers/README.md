# SI NATURAL Worker — free-tier deployment target

This is the first online-runtime adapter for the SI NATURAL workspace. It uses Cloudflare Workers + D1 and the Gemini Developer API. It is separate from the existing Python local MVP.

## Free-tier assumptions

- Cloudflare Workers Free currently documents up to 100,000 requests/day and 10 ms CPU per invocation. D1 has separate free-plan quotas. Limits can change; check current Cloudflare limits before relying on them.
- Gemini Developer API offers a free tier for selected models with limited rate limits. Free-tier terms may allow submitted content to be used to improve Google products. Do not send customer personal data, payment data, credentials, or confidential business records through this tier.
- No payment method or free-tier eligibility is guaranteed by this repository. The account owner must verify signup requirements.

## Deployment from GitHub Actions (no command line)

The repository includes `.github/workflows/deploy-si-natural-worker.yml`. It can apply the D1 schema and deploy the Worker in one manual workflow run.

Add these repository Actions secrets (GitHub → repository Settings → Secrets and variables → Actions):

- `CLOUDFLARE_API_TOKEN`: Cloudflare API token with only the required Workers Scripts Edit and D1 Edit permissions for this account. Avoid broad account-wide access if resource scoping is available.
- `CLOUDFLARE_ACCOUNT_ID`: Cloudflare account ID.
- `GEMINI_API_KEY`: key from Google AI Studio.

The workflow generates a random `API_TOKEN` itself and uploads it as a Worker secret; it is not stored in the repository or exposed to the browser.

Then open Actions → Deploy SI NATURAL Worker → Run workflow. The workflow installs dependencies, applies `schema.sql` to the existing D1 database, uploads the secrets, and deploys the Worker.

The Cloudflare D1 database ID is already configured in `wrangler.toml`.

## Routes

- `GET /health` — public health check.
- `GET /api/si_natural/tasks` — authenticated task history.
- `POST /api/si_natural/tasks` — authenticated AI task execution.
- `GET /api/si_natural/approvals` — authenticated pending approvals.
- `POST /api/si_natural/approvals/{task_id}/decision` — authenticated approval decision.

## Current scope and safety

- The Worker drafts and analyzes; it does not publish ads, change budgets/prices, send WhatsApp messages, issue refunds, or change external accounts.
- Those sensitive action categories are recorded as requiring CEO approval. Approval records are internal workflow state only; approving a record does not itself execute the external action.
- Shopify, EasyOrders, Meta Ads and WhatsApp adapters are not implemented yet.
- The existing static dashboard is still a prototype and is not connected to this API.
- The API uses a bearer token. The deployment workflow generates that token and stores it as a Worker secret, but does not expose it to the dashboard. Add a proper user authentication/access gateway before enabling browser access to private business data.

## Data handling

Use synthetic or anonymized data for Gemini free-tier requests. Add authenticated user identity, authorization, rate limits, backups, monitoring and an access gateway before using live customer data.
