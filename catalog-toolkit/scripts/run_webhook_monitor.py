#!/usr/bin/env python3
"""Run local Square webhook monitor (FastAPI + Uvicorn)."""

from __future__ import annotations

import os
from pathlib import Path
import sys

import uvicorn

SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from square_catalog_toolkit.webhook_monitor import create_app  # noqa: E402


def main() -> int:
    host = os.environ.get("SQUARE_WEBHOOK_MONITOR_HOST", "0.0.0.0")
    port = int(os.environ.get("SQUARE_WEBHOOK_MONITOR_PORT", "8087"))
    app = create_app()
    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
