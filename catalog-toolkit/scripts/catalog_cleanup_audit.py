#!/usr/bin/env python3
"""Audit category cleanup and site-channel assignment in Square catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections import Counter
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from square_catalog_toolkit.catalog_ops import FOOD_SOURCE_CATEGORIES  # noqa: E402
from square_catalog_toolkit.rest_client import SquareRestClient  # noqa: E402


DEFAULT_REQUIRED_CATEGORIES = [
    "Food & Pantry",
    "The General Store",
    "The Vintage Market",
    "New Arrivals",
]
DEFAULT_EXCLUDED_ALL_SITE_RULES = {"Analog"}
DEFAULT_FR_PREFIX = "🇫🇷"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Square category cleanup and online channel coverage."
    )
    parser.add_argument(
        "--require-category",
        action="append",
        default=[],
        help="Category name that must exist (repeatable).",
    )
    parser.add_argument(
        "--exclude-all-site-rule",
        action="append",
        default=[],
        help="Category exempt from all-site coverage requirement (repeatable).",
    )
    parser.add_argument(
        "--expect-new-finds-count",
        type=int,
        default=10,
        help="Expected item count in 'The New Finds' (default: 10).",
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit non-zero when issues are found.",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional path to write JSON output.",
    )
    return parser.parse_args()


def _category_ids_for_item(item: dict) -> list[str]:
    out: list[str] = []
    values = (item.get("item_data") or {}).get("categories") or []
    for value in values:
        if isinstance(value, dict):
            category_id = value.get("id")
            if category_id:
                out.append(category_id)
        elif isinstance(value, str):
            out.append(value)
    return out


def main() -> int:
    args = parse_args()
    required_categories = DEFAULT_REQUIRED_CATEGORIES + args.require_category
    excluded_all_site = DEFAULT_EXCLUDED_ALL_SITE_RULES | set(args.exclude_all_site_rule)

    client = SquareRestClient()
    categories = [obj for obj in client.list_catalog_objects_all(types="CATEGORY") if obj.get("type") == "CATEGORY"]
    items = [obj for obj in client.list_catalog_objects_all(types="ITEM") if obj.get("type") == "ITEM"]
    channels = client.list_channels().get("channels", [])
    sites = client.list_sites().get("sites", [])

    active_site_channels: dict[str, dict] = {}
    active_pos_channels: dict[str, dict] = {}
    for channel in channels:
        reference = channel.get("reference") or {}
        ref_type = reference.get("type")
        if channel.get("status") != "ACTIVE":
            continue
        if ref_type == "ONLINE_SITE":
            active_site_channels[channel["id"]] = channel
        elif ref_type == "POINT_OF_SALE":
            active_pos_channels[channel["id"]] = channel

    required_channel_ids = set(active_site_channels) | set(active_pos_channels)

    site_by_ref_id = {
        site["id"].replace("site_", ""): site
        for site in sites
        if isinstance(site.get("id"), str)
    }
    active_site_summary = {}
    for channel_id, channel in active_site_channels.items():
        ref_id = (channel.get("reference") or {}).get("id")
        site = site_by_ref_id.get(ref_id or "")
        active_site_summary[channel_id] = {
            "name": channel.get("name"),
            "domain": (site or {}).get("domain"),
            "site_title": (site or {}).get("site_title"),
            "is_published": (site or {}).get("is_published"),
        }

    item_counts = Counter()
    for item in items:
        for category_id in _category_ids_for_item(item):
            item_counts[category_id] += 1

    by_name: dict[str, dict] = {}
    category_rows: list[dict] = []
    for category in categories:
        category_data = category.get("category_data") or {}
        name = category_data.get("name")
        if not name:
            continue
        by_name[name] = category
        category_channels = category_data.get("channels") or []
        category_channel_ids = sorted(
            {
                value.get("id") if isinstance(value, dict) else value
                for value in category_channels
                if value
            }
        )
        category_rows.append(
            {
                "id": category["id"],
                "name": name,
                "items": item_counts.get(category["id"], 0),
                "online_visibility": category_data.get("online_visibility"),
                "channel_ids": category_channel_ids,
            }
        )
    category_rows.sort(key=lambda row: row["name"].lower())

    issues: dict[str, list | dict] = {
        "missing_required_categories": [],
        "legacy_food_not_empty": [],
        "legacy_food_not_hidden": [],
        "categories_with_items_hidden": [],
        "categories_with_items_missing_required_channels": [],
        "new_finds_count_mismatch": [],
    }

    for name in required_categories:
        if name not in by_name:
            issues["missing_required_categories"].append(name)

    for source_name in FOOD_SOURCE_CATEGORIES:
        category = by_name.get(source_name)
        if not category:
            continue
        category_data = category.get("category_data") or {}
        category_id = category.get("id")
        count = item_counts.get(category_id, 0)
        if count > 0:
            issues["legacy_food_not_empty"].append(
                {"name": source_name, "id": category_id, "items": count}
            )
        if category_data.get("online_visibility", False):
            issues["legacy_food_not_hidden"].append(
                {"name": source_name, "id": category_id, "online_visibility": True}
            )

    for row in category_rows:
        count = row["items"]
        if count <= 0:
            continue
        name = row["name"]
        if not row["online_visibility"]:
            issues["categories_with_items_hidden"].append(
                {"name": name, "id": row["id"], "items": count}
            )
        if name in excluded_all_site or name.startswith(DEFAULT_FR_PREFIX):
            continue
        missing_channels = sorted(set(required_channel_ids) - set(row["channel_ids"]))
        if missing_channels:
            issues["categories_with_items_missing_required_channels"].append(
                {
                    "name": name,
                    "id": row["id"],
                    "items": count,
                    "missing_channel_ids": missing_channels,
                }
            )

    new_finds = by_name.get("The New Finds")
    new_finds_count = 0
    if new_finds:
        new_finds_count = item_counts.get(new_finds["id"], 0)
        if args.expect_new_finds_count >= 0 and new_finds_count != args.expect_new_finds_count:
            issues["new_finds_count_mismatch"].append(
                {
                    "expected": args.expect_new_finds_count,
                    "actual": new_finds_count,
                    "category_id": new_finds["id"],
                }
            )

    issue_count = sum(len(value) for value in issues.values())
    payload = {
        "ok": issue_count == 0,
        "issue_count": issue_count,
        "active_site_channels": active_site_summary,
        "required_channel_ids": sorted(required_channel_ids),
        "new_finds_count": new_finds_count,
        "issues": issues,
        "categories": category_rows,
    }

    if args.json_out:
        out_path = Path(args.json_out).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(payload, indent=2))

    if args.fail_on_issues and issue_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
