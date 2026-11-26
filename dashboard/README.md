# Unified CEO Dashboard

The dashboard is one application with a business-context switcher. Selecting SI NATURAL or Paymob CRM changes the data connection and visible modules. The UI may be unified; the underlying databases and credentials remain separate.

The JSON file is a product specification, not a running dashboard. All business-scoped API requests must include and validate the selected business context server-side. Never trust a client-supplied business identifier without authorization checks.

Sensitive actions must create approval requests and remain pending until the CEO approves them.

## Preview locally or with GitHub Pages

This is a static front-end prototype:
- Open `index.html` in a browser to preview locally.
- To publish it, open the repository's **Settings → Pages**, choose **Deploy from a branch**, select `main` and folder `/dashboard`, then save. GitHub will provide the published URL after the deployment finishes.
- The page is mobile responsive and the workspace selector/navigation work in the browser.

Before production: replace sample placeholders with authenticated server API calls, add CEO login and server-side authorization, configure separate database credentials, implement approval endpoints, and remove demo-only UI states. Do not put database credentials, API tokens, customer lists or personal data in this public repository.
