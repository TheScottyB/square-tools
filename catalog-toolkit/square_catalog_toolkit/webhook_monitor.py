"""FastAPI scaffold for monitoring Square webhooks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import base64
import hashlib
import hmac
import json
import os
import sqlite3

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

SIGNATURE_HEADER = "x-square-hmacsha256-signature"


def verify_square_signature(
    *,
    signature_key: str,
    notification_url: str,
    request_body: bytes,
    provided_signature: str,
) -> bool:
    """
    Validate Square webhook signature using HMAC-SHA256.

    Per Square docs, the signature is generated from:
    - webhook signature key
    - notification URL
    - raw request body
    """
    message = notification_url.encode("utf-8") + request_body
    digest = hmac.new(signature_key.encode("utf-8"), message, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected, provided_signature)


@dataclass
class WebhookMonitorConfig:
    signature_key: str
    notification_url: str
    db_path: Path

    @classmethod
    def from_env(cls) -> "WebhookMonitorConfig":
        signature_key = os.environ.get("SQUARE_WEBHOOK_SIGNATURE_KEY", "").strip()
        notification_url = os.environ.get("SQUARE_WEBHOOK_NOTIFICATION_URL", "").strip()
        _default_db = str(Path(__file__).resolve().parent.parent / "data" / "webhook_events.db")
        db_path_raw = os.environ.get("SQUARE_WEBHOOK_MONITOR_DB", _default_db)
        db_path = Path(db_path_raw).expanduser()
        if not signature_key:
            raise RuntimeError("Missing SQUARE_WEBHOOK_SIGNATURE_KEY")
        if not notification_url:
            raise RuntimeError("Missing SQUARE_WEBHOOK_NOTIFICATION_URL")
        return cls(signature_key=signature_key, notification_url=notification_url, db_path=db_path)


def _init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS webhook_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              received_at TEXT NOT NULL,
              event_type TEXT,
              merchant_id TEXT,
              event_id TEXT,
              payload_json TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_webhook_events_received_at
            ON webhook_events(received_at DESC);
            """
        )


def _store_event(db_path: Path, payload: dict[str, Any]) -> None:
    data = payload.get("data") or {}
    event_type = payload.get("type")
    merchant_id = data.get("merchant_id") or data.get("merchantId")
    event_id = payload.get("event_id") or payload.get("eventId") or data.get("id")
    received_at = datetime.now(timezone.utc).isoformat()
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO webhook_events (received_at, event_type, merchant_id, event_id, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (received_at, event_type, merchant_id, event_id, raw),
        )
        conn.commit()


def _get_recent_events(db_path: Path, limit: int) -> list[dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, received_at, event_type, merchant_id, event_id, payload_json
            FROM webhook_events
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    events: list[dict[str, Any]] = []
    for row in rows:
        event = {
            "id": row[0],
            "received_at": row[1],
            "event_type": row[2],
            "merchant_id": row[3],
            "event_id": row[4],
            "payload": json.loads(row[5]),
        }
        events.append(event)
    return events


def create_app(config: WebhookMonitorConfig | None = None) -> FastAPI:
    cfg = config or WebhookMonitorConfig.from_env()
    _init_db(cfg.db_path)

    app = FastAPI(title="Square Webhook Monitor", version="0.1.0")

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        return {
            "ok": True,
            "notification_url": cfg.notification_url,
            "db_path": str(cfg.db_path),
        }

    @app.get("/events")
    async def events(limit: int = 50) -> dict[str, Any]:
        bounded = max(1, min(limit, 500))
        return {"events": _get_recent_events(cfg.db_path, bounded)}

    @app.post("/webhooks/square")
    async def square_webhook(request: Request) -> JSONResponse:
        provided_signature = request.headers.get(SIGNATURE_HEADER)
        if not provided_signature:
            raise HTTPException(status_code=400, detail=f"Missing {SIGNATURE_HEADER} header")

        raw_body = await request.body()
        is_valid = verify_square_signature(
            signature_key=cfg.signature_key,
            notification_url=cfg.notification_url,
            request_body=raw_body,
            provided_signature=provided_signature,
        )
        if not is_valid:
            raise HTTPException(status_code=403, detail="Invalid Square webhook signature")

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc}") from exc

        _store_event(cfg.db_path, payload)
        return JSONResponse({"ok": True})

    return app
