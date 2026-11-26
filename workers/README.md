# SI NATURAL Worker — free-tier deployment target

This is the first online-runtime adapter for the SI NATURAL workspace. It uses Cloudflare Workers + D1 and the Gemini Developer API. It is separate from the existing Python local MVP.

## Free-tier assumptions

- Cloudflare Workers Free currently documents up to 100,000 requests/day and 10 ms CPU per invocation. D1 has separate free-plan quotas. Limits can change; check the current Cloudflare pricing/limits before relying on it.
- Gemini Developer API offers a free tier for selected models with limited rate limits. The free-tier terms state submitted content may be used to improve Google products. Do not send customer personal data, payment data, credentials, or confidential business records through this tier.
- No payment method or free-tier eligibility is guaranteed by this repository. The account owner must verify the signup requirements.

## Deploy prerequisites

1. Create a Cloudflare account and a D1 database named `my-ai-company-si-natural`.
2. From this directory, install Wrangler and run `npx wrangler d1 create my-ai-company-si-natural`; put the returned database ID into `wrangler.toml`.
3. Run `npx wrangler d1 execute my-ai-company-si-natural --file=schema.sql --remote`.
4. Set secrets (never commit them):
   - `npx wrangler secret put API_TOKEN` — generate a long random token.
   - `npx wrangler secret put GEMINI_API_KEY` — key from Google AI Studio.
5. Deploy with `npx wrangler deploy`.
6. Set `ALLOWED_ORIGIN` to the exact GitHub Pages origin if browser access is enabled. Do not place API_TOKEN in dashboard JavaScript. A proper user login / Cloudflare Access gate must be added before exposing private business data to the public internet.

## Routes

- `GET /health` — public health check.
- `GET /api/si_natural/tasks` — authenticated task history.
- `POST /api/si_natural/tasks` — authenticated AI task execution.
- `GET /api/si_natural/approvals` — authenticated pending approvals.
- `POST /api/si_natural/approvals/{task_id}/decision` — authenticated approval decision.

The worker executes analysis and drafting tasks only. Sensitive actions are recorded as awaiting approval and are never executed against Meta, Shopify, EasyOrders or WhatsApp. Those external adapters are not implemented yet.

## Security notes

- The browser must never contain API_TOKEN or GEMINI_API_KEY.
- The current bearer-token API is suitable for controlled testing, not a public multi-user launch.
- The Gemini free tier is not suitable for confidential customer data; use synthetic or anonymized examples only.
- The current implementation stores business tasks and AI outputs in D1. Add authenticated user identity, authorization, rate limits, backups, monitoring and an access gateway before using live customer data.
