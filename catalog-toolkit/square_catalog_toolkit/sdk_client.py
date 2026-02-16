"""Version-locked Square SDK wrapper."""

from __future__ import annotations

from typing import Any
import uuid

from .auth import resolve_square_token
from .constants import API_VERSION

from square import Square
from square.environment import SquareEnvironment
from square.core.api_error import ApiError
from square.core.request_options import RequestOptions


class SquareSdkClient:
    """Python SDK wrapper that pins API version to the current release."""

    def __init__(
        self,
        token: str | None = None,
        *,
        api_version: str = API_VERSION,
        environment: SquareEnvironment = SquareEnvironment.PRODUCTION,
    ) -> None:
        self.token = resolve_square_token(token)
        self.api_version = api_version
        self.client = Square(
            environment=environment,
            token=self.token,
            version=self.api_version,
        )

    def request_options(self) -> RequestOptions:
        # Redundant with client.version, intentionally explicit for compliance.
        return RequestOptions(additional_headers={"Square-Version": self.api_version})

    # Catalog
    def list_categories(self) -> list[Any]:
        pager = self.client.catalog.list(types="CATEGORY", request_options=self.request_options())
        return list(pager)

    def list_items(self) -> list[Any]:
        pager = self.client.catalog.list(types="ITEM", request_options=self.request_options())
        return list(pager)

    def batch_upsert_catalog_objects(self, *, batches: list[dict[str, Any]]) -> Any:
        return self.client.catalog.batch_upsert(
            idempotency_key=str(uuid.uuid4()),
            batches=batches,
            request_options=self.request_options(),
        )

    # Channels/Sites
    def list_channels(self) -> list[Any]:
        pager = self.client.channels.list(request_options=self.request_options())
        return list(pager)

    def list_sites(self) -> Any:
        return self.client.sites.list(request_options=self.request_options())

    # Webhooks
    def list_webhook_event_types(self) -> Any:
        return self.client.webhooks.event_types.list(
            api_version=self.api_version,
            request_options=self.request_options(),
        )

    def list_webhook_subscriptions(self) -> list[Any]:
        pager = self.client.webhooks.subscriptions.list(request_options=self.request_options())
        return list(pager)

    def create_webhook_subscription(
        self,
        *,
        name: str,
        notification_url: str,
        event_types: list[str],
    ) -> Any:
        subscription = {
            "name": name,
            "enabled": True,
            "notification_url": notification_url,
            "event_types": event_types,
            "api_version": self.api_version,
        }
        return self.client.webhooks.subscriptions.create(
            idempotency_key=str(uuid.uuid4()),
            subscription=subscription,
            request_options=self.request_options(),
        )

    def test_webhook_subscription(self, *, subscription_id: str, event_type: str) -> Any:
        return self.client.webhooks.subscriptions.test(
            subscription_id=subscription_id,
            event_type=event_type,
            request_options=self.request_options(),
        )

    def rotate_webhook_signature_key(self, *, subscription_id: str) -> Any:
        return self.client.webhooks.subscriptions.update_signature_key(
            subscription_id=subscription_id,
            idempotency_key=str(uuid.uuid4()),
            request_options=self.request_options(),
        )

    @staticmethod
    def prove_invalid_version_rejected(token: str | None = None) -> tuple[bool, str]:
        """Return proof that API version header is enforced by Square."""
        resolved = resolve_square_token(token)
        invalid = Square(
            environment=SquareEnvironment.PRODUCTION,
            token=resolved,
            version="2099-99-99",
        )
        try:
            invalid.sites.list()
            return False, "Unexpected success; invalid version was not rejected."
        except ApiError as err:
            body = getattr(err, "body", {}) or {}
            code = ""
            if isinstance(body, dict):
                errors = body.get("errors") or []
                if errors and isinstance(errors[0], dict):
                    code = errors[0].get("code", "")
            ok = code == "INVALID_SQUARE_VERSION_FORMAT" or err.status_code == 400
            return ok, f"status={err.status_code} code={code or 'unknown'}"
