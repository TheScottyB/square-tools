#!/usr/bin/env python3
"""Bootstrap and manage Square webhook subscriptions (SDK)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from square_catalog_toolkit.constants import DOC_LINKS  # noqa: E402
from square_catalog_toolkit.sdk_client import SquareSdkClient  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Square webhook bootstrap utility.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List webhook event types and current subscriptions.")

    create = sub.add_parser("create", help="Create a webhook subscription.")
    create.add_argument("--name", required=True, help="Webhook subscription name.")
    create.add_argument("--notification-url", required=True, help="Public webhook URL.")
    create.add_argument(
        "--event-type",
        action="append",
        required=True,
        help="Event type to subscribe to (repeat for multiple).",
    )

    test = sub.add_parser("test", help="Send a test event to subscription URL.")
    test.add_argument("--subscription-id", required=True, help="Subscription ID.")
    test.add_argument(
        "--event-type",
        default="catalog.version.updated",
        help="Event type for test notification.",
    )

    rotate = sub.add_parser("rotate-signature-key", help="Rotate webhook signature key.")
    rotate.add_argument("--subscription-id", required=True, help="Subscription ID.")

    return parser


def command_list(client: SquareSdkClient) -> dict:
    event_types = client.list_webhook_event_types()
    subscriptions = client.list_webhook_subscriptions()
    event_names = []
    for event in (event_types.event_types or []):
        if isinstance(event, str):
            event_names.append(event)
        else:
            event_names.append(getattr(event, "name", str(event)))
    return {
        "docs": {
            "event_types": DOC_LINKS["list_webhook_event_types"],
            "subscriptions": DOC_LINKS["list_webhook_subscriptions"],
        },
        "event_types_count": len(event_types.event_types or []),
        "event_types": event_names,
        "subscriptions_count": len(subscriptions),
        "subscriptions": [
            {
                "id": sub.id,
                "name": sub.name,
                "enabled": sub.enabled,
                "notification_url": sub.notification_url,
                "event_types": sub.event_types,
                "api_version": sub.api_version,
            }
            for sub in subscriptions
        ],
    }


def command_create(client: SquareSdkClient, args: argparse.Namespace) -> dict:
    response = client.create_webhook_subscription(
        name=args.name,
        notification_url=args.notification_url,
        event_types=args.event_type,
    )
    sub = response.subscription
    return {
        "docs": DOC_LINKS["create_webhook_subscription"],
        "subscription": {
            "id": sub.id,
            "name": sub.name,
            "enabled": sub.enabled,
            "notification_url": sub.notification_url,
            "event_types": sub.event_types,
            "api_version": sub.api_version,
            "signature_key": sub.signature_key,
        },
    }


def command_test(client: SquareSdkClient, args: argparse.Namespace) -> dict:
    response = client.test_webhook_subscription(
        subscription_id=args.subscription_id,
        event_type=args.event_type,
    )
    if hasattr(response, "model_dump"):
        payload = response.model_dump()
    elif hasattr(response, "dict"):
        payload = response.dict()
    else:
        payload = {"raw": str(response)}
    return {
        "docs": DOC_LINKS["test_webhook_subscription"],
        "status_code": payload.get("status_code"),
        "passes_filter": payload.get("passes_filter"),
        "notification_url": payload.get("notification_url"),
        "payload": payload.get("payload"),
        "raw_response": payload,
    }


def command_rotate(client: SquareSdkClient, args: argparse.Namespace) -> dict:
    response = client.rotate_webhook_signature_key(subscription_id=args.subscription_id)
    return {
        "docs": DOC_LINKS["update_webhook_subscription_signature_key"],
        "status": response.status,
        "signature_key": response.signature_key,
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    client = SquareSdkClient()

    if args.command == "list":
        output = command_list(client)
    elif args.command == "create":
        output = command_create(client, args)
    elif args.command == "test":
        output = command_test(client, args)
    elif args.command == "rotate-signature-key":
        output = command_rotate(client, args)
    else:
        parser.error(f"Unknown command: {args.command}")
        return 2

    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
