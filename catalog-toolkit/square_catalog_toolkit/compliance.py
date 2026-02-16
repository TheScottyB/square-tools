"""Compliance checks for API version pinning and doc traceability."""

from __future__ import annotations

from typing import Any

from .constants import API_VERSION, DOC_LINKS
from .rest_client import SquareRestClient
from .sdk_client import SquareSdkClient


def run_rest_version_check() -> dict[str, Any]:
    client = SquareRestClient(api_version=API_VERSION)
    payload, response = client.list_catalog(types="CATEGORY", include_response=True)
    response_version = response.headers.get("square-version")
    return {
        "method": "REST",
        "request_square_version": API_VERSION,
        "response_square_version": response_version,
        "category_count": len(payload.get("objects") or []),
        "ok": response_version == API_VERSION,
        "docs": DOC_LINKS["list_catalog"],
    }


def run_sdk_version_check() -> dict[str, Any]:
    sdk = SquareSdkClient(api_version=API_VERSION)
    sites = sdk.list_sites()
    proof_ok, proof_detail = SquareSdkClient.prove_invalid_version_rejected()
    return {
        "method": "SDK",
        "sdk_client_version": API_VERSION,
        "sites_count": len(sites.sites or []),
        "invalid_version_rejected": proof_ok,
        "invalid_version_detail": proof_detail,
        "docs": DOC_LINKS["sdk_python_quickstart"],
    }


def docs_trace_for_core_calls() -> dict[str, str]:
    return {
        "list_catalog": DOC_LINKS["list_catalog"],
        "batch_upsert_catalog_objects": DOC_LINKS["batch_upsert_catalog_objects"],
        "search_catalog_items": DOC_LINKS["search_catalog_items"],
        "list_channels": DOC_LINKS["list_channels"],
        "list_sites": DOC_LINKS["list_sites"],
        "list_webhook_event_types": DOC_LINKS["list_webhook_event_types"],
        "list_webhook_subscriptions": DOC_LINKS["list_webhook_subscriptions"],
        "create_webhook_subscription": DOC_LINKS["create_webhook_subscription"],
        "test_webhook_subscription": DOC_LINKS["test_webhook_subscription"],
        "update_webhook_subscription_signature_key": DOC_LINKS[
            "update_webhook_subscription_signature_key"
        ],
        "validate_webhook_signatures": DOC_LINKS["validate_webhook_signatures"],
        "graphql": DOC_LINKS["graphql"],
    }
