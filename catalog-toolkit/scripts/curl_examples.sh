#!/usr/bin/env bash

set -euo pipefail

API_VERSION="2026-01-22"
BASE_URL="https://connect.squareup.com"

resolve_token() {
  if [[ -n "${SQUARE_ACCESS_TOKEN:-}" ]]; then
    printf "%s" "$SQUARE_ACCESS_TOKEN"
    return
  fi
  if [[ -n "${SQUARE_TOKEN:-}" ]]; then
    printf "%s" "$SQUARE_TOKEN"
    return
  fi
  local env_file="$HOME/.config/claude-mcp/.env"
  if [[ -f "$env_file" ]]; then
    local token
    token="$(awk -F= '/^SQUARE_ACCESS_TOKEN=/{print $2}' "$env_file" | tail -n1)"
    if [[ -z "$token" ]]; then
      token="$(awk -F= '/^SQUARE_TOKEN=/{print $2}' "$env_file" | tail -n1)"
    fi
    if [[ -n "$token" ]]; then
      printf "%s" "$token"
      return
    fi
  fi
  echo "Square token missing. Set SQUARE_ACCESS_TOKEN or SQUARE_TOKEN." >&2
  exit 1
}

TOKEN="$(resolve_token)"
COMMON_HEADERS=(
  -H "Authorization: Bearer ${TOKEN}"
  -H "Square-Version: ${API_VERSION}"
  -H "Content-Type: application/json"
)

usage() {
  cat <<'EOF'
Square curl examples (version-locked to 2026-01-22)

Docs:
- List catalog: https://developer.squareup.com/reference/square/catalog-api/list-catalog
- Batch upsert catalog objects: https://developer.squareup.com/reference/square/catalog-api/batch-upsert-catalog-objects
- List channels: https://developer.squareup.com/reference/square/channels-api/list-channels
- List sites: https://developer.squareup.com/reference/square/sites-api/list-sites
- List webhook event types: https://developer.squareup.com/reference/square/webhook-subscriptions-api/list-webhook-event-types
- List webhook subscriptions: https://developer.squareup.com/reference/square/webhook-subscriptions-api/list-webhook-subscriptions

Commands:
  list-categories
  list-items
  list-channels
  list-sites
  list-webhook-event-types
  list-webhook-subscriptions
EOF
}

cmd="${1:-}"
case "$cmd" in
  list-categories)
    curl -sS "${COMMON_HEADERS[@]}" \
      "${BASE_URL}/v2/catalog/list?types=CATEGORY" | jq
    ;;
  list-items)
    curl -sS "${COMMON_HEADERS[@]}" \
      "${BASE_URL}/v2/catalog/list?types=ITEM" | jq
    ;;
  list-channels)
    curl -sS "${COMMON_HEADERS[@]}" \
      "${BASE_URL}/v2/channels" | jq
    ;;
  list-sites)
    curl -sS "${COMMON_HEADERS[@]}" \
      "${BASE_URL}/v2/sites" | jq
    ;;
  list-webhook-event-types)
    curl -sS "${COMMON_HEADERS[@]}" \
      "${BASE_URL}/v2/webhooks/event-types?api_version=${API_VERSION}" | jq
    ;;
  list-webhook-subscriptions)
    curl -sS "${COMMON_HEADERS[@]}" \
      "${BASE_URL}/v2/webhooks/subscriptions" | jq
    ;;
  ""|-h|--help|help)
    usage
    ;;
  *)
    echo "Unknown command: $cmd" >&2
    usage
    exit 2
    ;;
esac
