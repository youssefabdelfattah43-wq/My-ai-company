# Database isolation

Create two independent PostgreSQL databases:
- `si_natural` using `db/si_natural/schema.sql`
- `paymob_crm` using `db/paymob_crm/schema.sql`

Do not place both businesses in one database. Use separate credentials and connection strings, each with the minimum required privileges. Keep credentials in the deployment secret manager or local untracked environment files, never in Git.

The Paymob CRM schema is for independently managed prospect and sales-pipeline records only; it does not imply access to Paymob internal systems.

Apply each schema only to its matching database. These SQL files have not yet been executed against a live PostgreSQL server.
