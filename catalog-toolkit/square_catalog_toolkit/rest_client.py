"""Version-locked REST client for Square APIs."""

from __future__ import annotations

from typing import Any
import json

import requests

from .auth import resolve_square_token
from .constants import API_VERSION, BASE_URL


class SquareRestClient:
    """Thin REST wrapper with strict Square-Version enforcement."""

    def __init__(
        self,
        token: str | None = None,
        *,
        api_version: str = API_VERSION,
        base_url: str = BASE_URL,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.token = resolve_square_token(token)
        self.api_version = api_version
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Square-Version": self.api_version,
            "Content-Type": "application/json",
        }

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        include_response: bool = False,
    ) -> Any:
        url = f"{self.base_url}{path}"
        response = requests.request(
            method=method.upper(),
            url=url,
            params=params,
            json=body,
            headers=self.headers,
            timeout=self.timeout_seconds,
        )

        response.raise_for_status()
        self._assert_response_version(response)

        try:
            payload: Any = response.json()
        except json.JSONDecodeError:
            payload = response.text

        if include_response:
            return payload, response
        return payload

    def _assert_response_version(self, response: requests.Response) -> None:
        returned = response.headers.get("square-version")
        if returned and returned != self.api_version:
            raise RuntimeError(
                f"Square version mismatch: expected {self.api_version}, got {returned}"
            )

    # Catalog
    def list_catalog(
        self,
        *,
        types: str | None = None,
        cursor: str | None = None,
        catalog_version: int | None = None,
        include_response: bool = False,
    ) -> Any:
        params: dict[str, Any] = {}
        if types:
            params["types"] = types
        if cursor:
            params["cursor"] = cursor
        if catalog_version is not None:
            params["catalog_version"] = catalog_version
        return self.request(
            "GET",
            "/v2/catalog/list",
            params=params or None,
            include_response=include_response,
        )

    def list_catalog_objects_all(self, *, types: str) -> list[dict[str, Any]]:
        objects: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            payload = self.list_catalog(types=types, cursor=cursor)
            objects.extend(payload.get("objects", []) or [])
            cursor = payload.get("cursor")
            if not cursor:
                break
        return objects

    def batch_upsert_catalog_objects(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/v2/catalog/batch-upsert", body=body)

    def upsert_catalog_object(
        self,
        *,
        object_payload: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        body = {
            "idempotency_key": idempotency_key,
            "object": object_payload,
        }
        return self.request("POST", "/v2/catalog/object", body=body)

    def search_catalog_items(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/v2/catalog/search-catalog-items", body=body)

    def retrieve_catalog_object(self, object_id: str) -> dict[str, Any]:
        return self.request("GET", f"/v2/catalog/object/{object_id}")

    # Channels/Sites
    def list_channels(self) -> dict[str, Any]:
        return self.request("GET", "/v2/channels")

    def list_sites(self) -> dict[str, Any]:
        return self.request("GET", "/v2/sites")

    # Webhooks
    def list_webhook_event_types(self, *, api_version: str | None = None) -> dict[str, Any]:
        params = {"api_version": api_version} if api_version else None
        return self.request("GET", "/v2/webhooks/event-types", params=params)

    def list_webhook_subscriptions(
        self,
        *,
        cursor: str | None = None,
        include_disabled: bool | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if cursor:
            params["cursor"] = cursor
        if include_disabled is not None:
            params["include_disabled"] = str(include_disabled).lower()
        if limit is not None:
            params["limit"] = limit
        return self.request(
            "GET",
            "/v2/webhooks/subscriptions",
            params=params or None,
        )

    def create_webhook_subscription(
        self,
        *,
        idempotency_key: str,
        subscription: dict[str, Any],
    ) -> dict[str, Any]:
        body = {
            "idempotency_key": idempotency_key,
            "subscription": subscription,
        }
        return self.request("POST", "/v2/webhooks/subscriptions", body=body)

    def test_webhook_subscription(
        self,
        *,
        subscription_id: str,
        event_type: str | None = None,
    ) -> dict[str, Any]:
        body = {"event_type": event_type} if event_type else {}
        return self.request(
            "POST",
            f"/v2/webhooks/subscriptions/{subscription_id}/test",
            body=body,
        )

    def update_webhook_subscription_signature_key(
        self,
        *,
        subscription_id: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        body = {"idempotency_key": idempotency_key}
        return self.request(
            "POST",
            f"/v2/webhooks/subscriptions/{subscription_id}/signature-key",
            body=body,
        )
