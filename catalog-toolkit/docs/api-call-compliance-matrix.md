# API Call Compliance Matrix

This matrix maps each API call in the toolkit to:

- Official Square docs
- Code location in this toolkit
- Versioning compliance mechanism

## Version policy

- Required version: `2026-01-22`
- REST: explicit `Square-Version` header
- SDK: `Square(version="2026-01-22")` plus per-call `RequestOptions(additional_headers={"Square-Version":"2026-01-22"})`

## Calls

| Call | Docs | Code |
|---|---|---|
| `GET /v2/catalog/list` | [List catalog](https://developer.squareup.com/reference/square/catalog-api/list-catalog) | `/Users/scottybe/workspace/square/square-tools/catalog-toolkit/square_catalog_toolkit/rest_client.py` |
| `POST /v2/catalog/batch-upsert` | [Batch upsert catalog objects](https://developer.squareup.com/reference/square/catalog-api/batch-upsert-catalog-objects) | `/Users/scottybe/workspace/square/square-tools/catalog-toolkit/square_catalog_toolkit/rest_client.py` |
| `POST /v2/catalog/search-catalog-items` | [Search catalog items](https://developer.squareup.com/reference/square/catalog-api/search-catalog-items) | `/Users/scottybe/workspace/square/square-tools/catalog-toolkit/square_catalog_toolkit/rest_client.py` |
| `GET /v2/catalog/object/{id}` | [Retrieve catalog object](https://developer.squareup.com/reference/square/catalog-api/retrieve-catalog-object) | `/Users/scottybe/workspace/square/square-tools/catalog-toolkit/square_catalog_toolkit/rest_client.py` |
| `GET /v2/channels` | [List channels](https://developer.squareup.com/reference/square/channels-api/list-channels) | `/Users/scottybe/workspace/square/square-tools/catalog-toolkit/square_catalog_toolkit/rest_client.py` |
| `GET /v2/sites` | [List sites](https://developer.squareup.com/reference/square/sites-api/list-sites) | `/Users/scottybe/workspace/square/square-tools/catalog-toolkit/square_catalog_toolkit/rest_client.py` |
| `GET /v2/webhooks/event-types` | [List webhook event types](https://developer.squareup.com/reference/square/webhook-subscriptions-api/list-webhook-event-types) | `/Users/scottybe/workspace/square/square-tools/catalog-toolkit/square_catalog_toolkit/rest_client.py` |
| `GET /v2/webhooks/subscriptions` | [List webhook subscriptions](https://developer.squareup.com/reference/square/webhook-subscriptions-api/list-webhook-subscriptions) | `/Users/scottybe/workspace/square/square-tools/catalog-toolkit/square_catalog_toolkit/rest_client.py` |
| `POST /v2/webhooks/subscriptions` | [Create webhook subscription](https://developer.squareup.com/reference/square/webhook-subscriptions-api/create-webhook-subscription) | `/Users/scottybe/workspace/square/square-tools/catalog-toolkit/square_catalog_toolkit/rest_client.py` |
| `POST /v2/webhooks/subscriptions/{id}/test` | [Test webhook subscription](https://developer.squareup.com/reference/square/webhook-subscriptions-api/test-webhook-subscription) | `/Users/scottybe/workspace/square/square-tools/catalog-toolkit/square_catalog_toolkit/rest_client.py` |
| `POST /v2/webhooks/subscriptions/{id}/signature-key` | [Update webhook subscription signature key](https://developer.squareup.com/reference/square/webhook-subscriptions-api/update-webhook-subscription-signature-key) | `/Users/scottybe/workspace/square/square-tools/catalog-toolkit/square_catalog_toolkit/rest_client.py` |
| Webhook request signature validation | [Validate and debug webhook events](https://developer.squareup.com/docs/webhooks/step3validate) | `/Users/scottybe/workspace/square/square-tools/catalog-toolkit/square_catalog_toolkit/webhook_monitor.py` |

## Compliance proof script

Run:

```bash
python3 /Users/scottybe/workspace/square/square-tools/catalog-toolkit/scripts/compliance_check.py
```

Expected proof points:

1. REST response header echoes `square-version: 2026-01-22`.
2. SDK call succeeds with `version="2026-01-22"`.
3. SDK call fails with `version="2099-99-99"` and returns `INVALID_SQUARE_VERSION_FORMAT`.
