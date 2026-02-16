#!/usr/bin/env python3
"""Run SDK/REST version compliance checks and print docs traceability."""

from __future__ import annotations

import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from square_catalog_toolkit.compliance import (  # noqa: E402
    docs_trace_for_core_calls,
    run_rest_version_check,
    run_sdk_version_check,
)
from square_catalog_toolkit.constants import API_VERSION, DOC_LINKS  # noqa: E402


def main() -> int:
    rest = run_rest_version_check()
    sdk = run_sdk_version_check()
    docs = docs_trace_for_core_calls()

    ok = bool(rest.get("ok")) and bool(sdk.get("invalid_version_rejected"))

    output = {
        "policy": {
            "api_version": API_VERSION,
            "versioning_doc": DOC_LINKS["versioning_overview"],
            "release_doc": DOC_LINKS["release_2026_01_22"],
        },
        "checks": {
            "rest": rest,
            "sdk": sdk,
        },
        "docs": docs,
        "ok": ok,
    }
    print(json.dumps(output, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
