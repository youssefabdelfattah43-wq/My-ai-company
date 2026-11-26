# Unified CEO Dashboard

The dashboard is one application with a business-context switcher. Selecting SI NATURAL or Paymob CRM changes the data connection and visible modules. The UI may be unified; the underlying databases and credentials remain separate.

The JSON file is a product specification, not a running dashboard. All business-scoped API requests must include and validate the selected business context server-side. Never trust a client-supplied business identifier without authorization checks.

Sensitive actions must create approval requests and remain pending until the CEO approves them.
