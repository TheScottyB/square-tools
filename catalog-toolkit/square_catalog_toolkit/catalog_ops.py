"""Reusable catalog/category operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import uuid

from .rest_client import SquareRestClient


FOOD_SOURCE_CATEGORIES = [
    "Chips & Crisps",
    "Cookies & Sweets",
    "Drinks",
    "Asian Imports",
]
DEFAULT_FOOD_TARGET = "Food & Pantry"
DEFAULT_CHANNEL_TEMPLATE = "The New Finds"


@dataclass
class MergePlan:
    target_name: str
    target_id: str | None
    source_name_to_id: dict[str, str]
    source_ids: set[str]
    affected_items: list[dict[str, Any]]
    category_created: bool = False
    created_category_id: str | None = None


def _chunked(items: list[Any], size: int) -> list[list[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _extract_category_ids(item: dict[str, Any]) -> list[str]:
    raw = (item.get("item_data") or {}).get("categories") or []
    ids: list[str] = []
    for value in raw:
        if isinstance(value, dict):
            category_id = value.get("id")
            if category_id:
                ids.append(category_id)
        elif isinstance(value, str):
            ids.append(value)
    return ids


def _index_categories(categories: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    by_id: dict[str, dict[str, Any]] = {}
    by_name: dict[str, str] = {}
    for category in categories:
        if category.get("type") != "CATEGORY":
            continue
        category_id = category.get("id")
        name = (category.get("category_data") or {}).get("name")
        if not category_id or not name:
            continue
        by_id[category_id] = category
        by_name[name] = category_id
    return by_id, by_name


def _build_item_update(
    item: dict[str, Any],
    *,
    new_category_ids: list[str],
    source_ids: set[str],
    target_id: str,
) -> dict[str, Any]:
    item_data = item.get("item_data") or {}
    update_data: dict[str, Any] = {
        "name": item_data.get("name", item.get("id", "Unnamed item")),
        "categories": [{"id": category_id} for category_id in new_category_ids],
    }
    # Square can require an ITEM to include variations in some upsert paths.
    # Preserve existing variations to avoid item shape validation failures.
    if item_data.get("variations"):
        update_data["variations"] = item_data.get("variations")

    reporting = item_data.get("reporting_category")
    if isinstance(reporting, dict):
        reporting_id = reporting.get("id")
        if reporting_id in source_ids:
            update_data["reporting_category"] = {"id": target_id}

    return {
        "type": "ITEM",
        "id": item["id"],
        "version": item["version"],
        "item_data": update_data,
    }


def snapshot_items(
    client: SquareRestClient,
    *,
    item_ids: set[str] | None = None,
    output_dir: Path | None = None,
) -> Path:
    """Persist a rollback-friendly snapshot of current item categories."""
    items = client.list_catalog_objects_all(types="ITEM")
    if item_ids:
        items = [item for item in items if item.get("id") in item_ids]

    payload = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "items": [
            {
                "id": item.get("id"),
                "version": item.get("version"),
                "name": (item.get("item_data") or {}).get("name"),
                "categories": (item.get("item_data") or {}).get("categories"),
                "reporting_category": (item.get("item_data") or {}).get("reporting_category"),
            }
            for item in items
        ],
    }

    target_dir = output_dir or Path.cwd()
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / f"catalog-snapshot-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def plan_merge_categories(
    client: SquareRestClient,
    *,
    source_names: list[str],
    target_name: str,
) -> MergePlan:
    categories = client.list_catalog_objects_all(types="CATEGORY")
    items = client.list_catalog_objects_all(types="ITEM")

    _, by_name = _index_categories(categories)

    source_name_to_id: dict[str, str] = {}
    for name in source_names:
        category_id = by_name.get(name)
        if not category_id:
            raise RuntimeError(f"Source category not found: {name}")
        source_name_to_id[name] = category_id

    source_ids = set(source_name_to_id.values())
    target_id = by_name.get(target_name)

    affected_items: list[dict[str, Any]] = []
    for item in items:
        current_ids = _extract_category_ids(item)
        if not any(category_id in source_ids for category_id in current_ids):
            continue

        new_ids = [category_id for category_id in current_ids if category_id not in source_ids]
        if target_id and target_id not in new_ids:
            new_ids.append(target_id)

        affected_items.append(
            {
                "item_id": item.get("id"),
                "name": (item.get("item_data") or {}).get("name"),
                "old_category_ids": current_ids,
                "new_category_ids": new_ids,
            }
        )

    return MergePlan(
        target_name=target_name,
        target_id=target_id,
        source_name_to_id=source_name_to_id,
        source_ids=source_ids,
        affected_items=affected_items,
    )


def ensure_category(
    client: SquareRestClient,
    *,
    category_name: str,
    channel_template_name: str = DEFAULT_CHANNEL_TEMPLATE,
) -> str:
    categories = client.list_catalog_objects_all(types="CATEGORY")
    by_id, by_name = _index_categories(categories)
    existing_id = by_name.get(category_name)
    if existing_id:
        return existing_id

    template_id = by_name.get(channel_template_name)
    if not template_id:
        raise RuntimeError(
            f"Cannot create category '{category_name}' because template category "
            f"'{channel_template_name}' was not found."
        )
    template_channels = ((by_id[template_id].get("category_data") or {}).get("channels") or [])

    payload = {
        "idempotency_key": str(uuid.uuid4()),
        "sparse_update": True,
        "batches": [
            {
                "objects": [
                    {
                        "type": "CATEGORY",
                        "id": f"#tmp_{category_name.lower().replace(' ', '_').replace('&', 'and')}",
                        "category_data": {
                            "name": category_name,
                            "online_visibility": True,
                            "channels": template_channels,
                        },
                    }
                ]
            }
        ],
    }
    response = client.batch_upsert_catalog_objects(payload)
    mappings = response.get("id_mappings") or []
    if not mappings:
        raise RuntimeError(f"Failed to create category: {category_name}")
    return mappings[0]["object_id"]


def apply_merge_plan(
    client: SquareRestClient,
    plan: MergePlan,
    *,
    create_target_if_missing: bool = True,
    batch_size: int = 20,
) -> dict[str, Any]:
    if not plan.target_id:
        if not create_target_if_missing:
            raise RuntimeError(f"Target category '{plan.target_name}' does not exist.")
        created_id = ensure_category(client, category_name=plan.target_name)
        plan.target_id = created_id
        plan.category_created = True
        plan.created_category_id = created_id

    if not plan.target_id:
        raise RuntimeError("Target category ID is missing after ensure-category step.")

    all_items = client.list_catalog_objects_all(types="ITEM")
    by_id = {item["id"]: item for item in all_items if item.get("type") == "ITEM"}

    updates: list[dict[str, Any]] = []
    for affected in plan.affected_items:
        item = by_id.get(affected["item_id"])
        if not item:
            continue
        current_ids = _extract_category_ids(item)
        new_ids = [category_id for category_id in current_ids if category_id not in plan.source_ids]
        if plan.target_id not in new_ids:
            new_ids.append(plan.target_id)

        if current_ids == new_ids:
            continue

        item_full = json.loads(json.dumps(item))
        item_data = item_full.get("item_data") or {}
        item_data["categories"] = [{"id": category_id} for category_id in new_ids]
        reporting = item_data.get("reporting_category")
        if isinstance(reporting, dict) and reporting.get("id") in plan.source_ids:
            item_data["reporting_category"] = {"id": plan.target_id}
        item_full["item_data"] = item_data
        updates.append(item_full)

    # Catalog upsert on full ITEM object avoids validation edge-cases for partial ITEM updates.
    for item_obj in updates:
        client.upsert_catalog_object(
            object_payload=item_obj,
            idempotency_key=str(uuid.uuid4()),
        )

    return {
        "target_category": plan.target_name,
        "target_category_id": plan.target_id,
        "source_categories": plan.source_name_to_id,
        "items_updated": len(updates),
        "category_created": plan.category_created,
        "created_category_id": plan.created_category_id,
    }


def merge_food_categories(
    client: SquareRestClient,
    *,
    target_name: str = DEFAULT_FOOD_TARGET,
    apply: bool = False,
    snapshot_dir: Path | None = None,
) -> dict[str, Any]:
    plan = plan_merge_categories(
        client,
        source_names=FOOD_SOURCE_CATEGORIES,
        target_name=target_name,
    )

    affected_item_ids = {item["item_id"] for item in plan.affected_items}
    snapshot_path = snapshot_items(client, item_ids=affected_item_ids, output_dir=snapshot_dir)

    summary: dict[str, Any] = {
        "mode": "apply" if apply else "dry-run",
        "target_name": target_name,
        "target_id": plan.target_id,
        "source_categories": plan.source_name_to_id,
        "affected_items": len(plan.affected_items),
        "snapshot_path": str(snapshot_path),
    }

    if not apply:
        return summary

    result = apply_merge_plan(client, plan)
    summary["result"] = result
    return summary
