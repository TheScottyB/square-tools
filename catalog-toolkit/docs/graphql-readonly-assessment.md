# Square GraphQL Read-Only Assessment

Date: 2026-02-16  
Target API baseline: `2026-01-22`

## Sources

- [Square GraphQL](https://developer.squareup.com/docs/devtools/graphql)
- [GraphQL query examples](https://developer.squareup.com/docs/graphql/query-examples)
- [Square APIs reference (for mutation/update paths)](https://developer.squareup.com/reference/square)

## Findings

1. Square GraphQL is suitable for read-heavy reporting and search-style aggregation.
2. GraphQL supports query operations and does not replace write workflows needed for catalog updates.
3. Write/update operations (catalog/category changes, webhook subscription management, etc.) should stay on REST APIs.

## Endpoint and Auth

- Production GraphQL endpoint: `https://connect.squareup.com/public/graphql`
- Sandbox GraphQL endpoint: `https://connect.squareupsandbox.com/public/graphql`
- Auth: same Bearer access token pattern as REST APIs.

## Recommended architecture for a read-only app

1. Query-only service layer
- Wrap GraphQL in a service that exposes approved read models to UI/jobs.
- Persist only needed fields for performance dashboards.

2. Persisted/allowlisted queries
- Keep a query allowlist in source control.
- Block arbitrary query text in production to avoid accidental broad data pulls.

3. Keep writes on REST
- Use REST APIs for create/update/delete workflows.
- Use GraphQL strictly for browsing/reporting and operator insights.

4. Webhook + GraphQL combination
- Use webhooks to trigger lightweight refresh jobs.
- Use GraphQL to fetch read-model slices after an event arrives.

## Practical next step

- Start with one read-only dashboard:
  - catalog category/item counts
  - recent order/customer summaries
  - stale inventory candidates
- Keep all category merge/publish operations in REST/SDK tooling from this toolkit.
