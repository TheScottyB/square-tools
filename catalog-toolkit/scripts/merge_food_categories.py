#!/usr/bin/env python3
"""Merge food categories into a single target category."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from square_catalog_toolkit.catalog_ops import DEFAULT_FOOD_TARGET, merge_food_categories  # noqa: E402
from square_catalog_toolkit.rest_client import SquareRestClient  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge food categories into a target category.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview only (default).")
    mode.add_argument("--apply", action="store_true", help="Apply updates to Square.")
    parser.add_argument(
        "--target-name",
        default=DEFAULT_FOOD_TARGET,
        help=f"Target category name (default: {DEFAULT_FOOD_TARGET}).",
    )
    parser.add_argument(
        "--snapshot-dir",
        default=str(SCRIPT_DIR.parent / "data" / "snapshots"),
        help="Directory for rollback snapshots.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    apply_mode = bool(args.apply)
    client = SquareRestClient()

    result = merge_food_categories(
        client,
        target_name=args.target_name,
        apply=apply_mode,
        snapshot_dir=Path(args.snapshot_dir),
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
