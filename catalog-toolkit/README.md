# Square Catalog Toolkit (Version-Locked)

Reusable Square API toolkit for catalog/category operations, compliance checks, webhook monitoring scaffolding, and GraphQL read-only planning.

This toolkit is pinned to:

- `Square-Version: 2026-01-22`
- Python SDK `squareup==44.0.1.20260122`

## Why this exists

- Reuse by agents/skills without re-implementing auth/versioning.
- Keep all scripts compliant with the current API release.
- Provide both SDK and curl-compatible workflows.
- Scaffold webhook monitoring for catalog/account changes.

## Layout

```text
catalog-toolkit/
  docs/
    graphql-readonly-assessment.md
  scripts/
    catalog_cleanup_audit.py
    compliance_check.py
    merge_food_categories.py
    webhook_bootstrap.py
    run_webhook_monitor.py
    curl_examples.sh
  square_catalog_toolkit/
    __init__.py
    auth.py
    catalog_ops.py
    compliance.py
    constants.py
    rest_client.py
    sdk_client.py
    webhook_monitor.py
  requirements.txt
```

## Install

```bash
cd /Users/scottybe/workspace/square/square-tools/catalog-toolkit
python3 -m pip install -r requirements.txt
```

Auth is read from:

- `SQUARE_ACCESS_TOKEN` (preferred)
- `SQUARE_TOKEN` (fallback)
- `~/.config/claude-mcp/.env` (fallback parser)

## Runbook

### 1) Prove API-version compliance

```bash
python3 /Users/scottybe/workspace/square/square-tools/catalog-toolkit/scripts/compliance_check.py
```

This runs:

- REST call with explicit `Square-Version: 2026-01-22` and verifies response header.
- SDK call with `version="2026-01-22"`.
- SDK negative test (`version="2099-99-99"`) that must fail with `INVALID_SQUARE_VERSION_FORMAT`.

### 2) Category merge dry-run/apply

```bash
# dry run
python3 /Users/scottybe/workspace/square/square-tools/catalog-toolkit/scripts/merge_food_categories.py --dry-run

# apply
python3 /Users/scottybe/workspace/square/square-tools/catalog-toolkit/scripts/merge_food_categories.py --apply
```

Default merge:

- Source categories: `Chips & Crisps`, `Cookies & Sweets`, `Drinks`, `Asian Imports`
- Target category: `Food & Pantry`

### 3) Webhook bootstrap

```bash
# list available event types and active subscriptions
python3 /Users/scottybe/workspace/square/square-tools/catalog-toolkit/scripts/webhook_bootstrap.py list

# create a subscription
python3 /Users/scottybe/workspace/square/square-tools/catalog-toolkit/scripts/webhook_bootstrap.py create \
  --name "Catalog Monitor" \
  --notification-url "https://example.com/webhooks/square" \
  --event-type "catalog.version.updated"

# send a test event
python3 /Users/scottybe/workspace/square/square-tools/catalog-toolkit/scripts/webhook_bootstrap.py test \
  --subscription-id "<SUBSCRIPTION_ID>" \
  --event-type "catalog.version.updated"
```

### 4) Audit category cleanup and site assignments

```bash
python3 /Users/scottybe/workspace/square/square-tools/catalog-toolkit/scripts/catalog_cleanup_audit.py --fail-on-issues
```

Checks:

- Required categories exist (`Food & Pantry`, `The General Store`, `The Vintage Market`, `New Arrivals`)
- Legacy food categories are empty + hidden
- Categories with items are visible and assigned to active site/POS channels
- `The New Finds` count matches expected intake cap (default `10`)

### 5) Run webhook monitor scaffold

```bash
export SQUARE_WEBHOOK_NOTIFICATION_URL="https://example.com/webhooks/square"
export SQUARE_WEBHOOK_SIGNATURE_KEY="<SIGNATURE_KEY>"

python3 /Users/scottybe/workspace/square/square-tools/catalog-toolkit/scripts/run_webhook_monitor.py
```

Endpoints:

- `GET /healthz`
- `POST /webhooks/square`
- `GET /events?limit=50`

## API calls + docs (one link per call)

| Call | Endpoint | Docs |
|---|---|---|
| List categories/items | `GET /v2/catalog/list` | [List catalog](https://developer.squareup.com/reference/square/catalog-api/list-catalog) |
| Batch updates/creates | `POST /v2/catalog/batch-upsert` | [Batch upsert catalog objects](https://developer.squareup.com/reference/square/catalog-api/batch-upsert-catalog-objects) |
| Search items | `POST /v2/catalog/search-catalog-items` | [Search catalog items](https://developer.squareup.com/reference/square/catalog-api/search-catalog-items) |
| Retrieve object | `GET /v2/catalog/object/{id}` | [Retrieve catalog object](https://developer.squareup.com/reference/square/catalog-api/retrieve-catalog-object) |
| Channel visibility mapping | `GET /v2/channels` | [List channels](https://developer.squareup.com/reference/square/channels-api/list-channels) |
| Site inventory | `GET /v2/sites` | [List sites](https://developer.squareup.com/reference/square/sites-api/list-sites) |
| Webhook event types | `GET /v2/webhooks/event-types` | [List webhook event types](https://developer.squareup.com/reference/square/webhook-subscriptions-api/list-webhook-event-types) |
| List webhook subscriptions | `GET /v2/webhooks/subscriptions` | [List webhook subscriptions](https://developer.squareup.com/reference/square/webhook-subscriptions-api/list-webhook-subscriptions) |
| Create webhook subscription | `POST /v2/webhooks/subscriptions` | [Create webhook subscription](https://developer.squareup.com/reference/square/webhook-subscriptions-api/create-webhook-subscription) |
| Test webhook subscription | `POST /v2/webhooks/subscriptions/{id}/test` | [Test webhook subscription](https://developer.squareup.com/reference/square/webhook-subscriptions-api/test-webhook-subscription) |
| Rotate signature key | `POST /v2/webhooks/subscriptions/{id}/signature-key` | [Update webhook subscription signature key](https://developer.squareup.com/reference/square/webhook-subscriptions-api/update-webhook-subscription-signature-key) |
| Webhook signature validation | request header/body verification | [Validate and debug webhook events](https://developer.squareup.com/docs/webhooks/step3validate) |
| API versioning rules | `Square-Version` behavior | [Versioning overview](https://developer.squareup.com/docs/build-basics/versioning-overview) |
| Latest release target | `2026-01-22` | [Connect API changelog (2026-01-22)](https://developer.squareup.com/docs/changelog/connect-logs/2026-01-22) |
| Python SDK usage | SDK client/config patterns | [Python SDK quickstart](https://developer.squareup.com/docs/sdks/python/quick-start) |
| GraphQL (read-only) | query endpoint/planning | [Square GraphQL](https://developer.squareup.com/docs/devtools/graphql) |

## Compliance policy

- Every REST request includes `Square-Version: 2026-01-22`.
- SDK client is initialized with `version="2026-01-22"`.
- Compliance script proves mis-versioned SDK calls fail, ensuring version locking is active.
