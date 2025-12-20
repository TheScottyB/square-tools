#!/usr/bin/env python3

"""
Square Items MongoDB Cache Manager
==================================

This system caches Square catalog items locally in MongoDB, tracking changes
and providing before/after snapshots for items that need updates.

Features:
- Sync Square catalog items to local MongoDB cache
- Track item changes with before/after snapshots
- Detect items that need updates
- Provide diff reports for changed items
- Maintain change history and audit trail
"""

import os
import sys
import json
import requests
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pymongo import MongoClient
from pymongo.collection import Collection

@dataclass
class ChangeSnapshot:
    """Represents a before/after snapshot of an item change"""
    item_id: str
    item_name: str
    change_type: str  # 'create', 'update', 'delete'
    timestamp: datetime
    before_data: Optional[Dict] = None
    after_data: Optional[Dict] = None
    differences: Optional[Dict] = None
    square_version_before: Optional[int] = None
    square_version_after: Optional[int] = None

class SquareCacheManager:
    """Manages Square catalog items in MongoDB cache"""
    
    def __init__(self, square_token: str, mongo_uri: str = "mongodb://localhost:27017/"):
        self.square_token = square_token
        self.square_base_url = "https://connect.squareup.com/v2"
        self.headers = {
            "Square-Version": "2024-09-18",
            "Authorization": f"Bearer {square_token}",
            "Content-Type": "application/json"
        }
        
        # Connect to MongoDB
        self.client = MongoClient(mongo_uri)
        self.db = self.client['square_cache']
        
        # Collections
        self.items_collection = self.db['catalog_items']
        self.changes_collection = self.db['change_snapshots']
        self.sync_log_collection = self.db['sync_log']
        
        # Create indexes for performance
        self._create_indexes()
        
    def _create_indexes(self):
        """Create MongoDB indexes for optimal performance"""
        # Items collection indexes
        self.items_collection.create_index("id", unique=True)
        self.items_collection.create_index("updated_at")
        self.items_collection.create_index("version")
        self.items_collection.create_index("item_data.name")
        
        # Changes collection indexes
        self.changes_collection.create_index("item_id")
        self.changes_collection.create_index("timestamp")
        self.changes_collection.create_index("change_type")
        
        # Sync log indexes
        self.sync_log_collection.create_index("timestamp")
        
    def _calculate_hash(self, data: Dict) -> str:
        """Calculate SHA256 hash of item data for change detection"""
        # Remove volatile fields that shouldn't trigger change detection
        clean_data = data.copy()
        if 'updated_at' in clean_data:
            del clean_data['updated_at']
        if 'version' in clean_data:
            del clean_data['version']
            
        json_str = json.dumps(clean_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _fetch_square_items(self) -> List[Dict]:
        """Fetch all catalog items from Square API"""
        items = []
        cursor = None
        
        while True:
            url = f"{self.square_base_url}/catalog/list?types=ITEM"
            if cursor:
                url += f"&cursor={cursor}"
                
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            if 'objects' in data:
                items.extend(data['objects'])
                
            cursor = data.get('cursor')
            if not cursor:
                break
                
        return items
    
    def _detect_changes(self, square_item: Dict) -> Optional[ChangeSnapshot]:
        """Detect changes between Square item and cached version"""
        item_id = square_item['id']
        cached_item = self.items_collection.find_one({"id": item_id})
        
        if not cached_item:
            # New item
            return ChangeSnapshot(
                item_id=item_id,
                item_name=square_item.get('item_data', {}).get('name', 'Unknown'),
                change_type='create',
                timestamp=datetime.now(timezone.utc),
                before_data=None,
                after_data=square_item,
                square_version_after=square_item.get('version')
            )
        
        # Check if item has changed (excluding volatile fields)
        square_hash = self._calculate_hash(square_item)
        cached_hash = cached_item.get('content_hash', '')
        
        if square_hash != cached_hash:
            # Item updated
            differences = self._find_differences(cached_item, square_item)
            
            return ChangeSnapshot(
                item_id=item_id,
                item_name=square_item.get('item_data', {}).get('name', 'Unknown'),
                change_type='update',
                timestamp=datetime.now(timezone.utc),
                before_data=cached_item,
                after_data=square_item,
                differences=differences,
                square_version_before=cached_item.get('version'),
                square_version_after=square_item.get('version')
            )
            
        return None
    
    def _find_differences(self, before: Dict, after: Dict) -> Dict:
        """Find specific differences between before and after data"""
        differences = {}
        
        # Compare key fields
        compare_fields = [
            'item_data.name',
            'item_data.description', 
            'item_data.image_ids',
            'item_data.variations',
            'item_data.categories',
            'version',
            'updated_at'
        ]
        
        for field_path in compare_fields:
            before_val = self._get_nested_value(before, field_path)
            after_val = self._get_nested_value(after, field_path)
            
            if before_val != after_val:
                differences[field_path] = {
                    'before': before_val,
                    'after': after_val
                }
                
        return differences
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get nested value from dict using dot notation"""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
                
        return value
    
    def sync_from_square(self) -> Dict[str, Any]:
        """Sync all items from Square to MongoDB cache"""
        print("🔄 Starting Square catalog sync...")
        
        sync_start = datetime.now(timezone.utc)
        
        try:
            # Fetch all items from Square
            square_items = self._fetch_square_items()
            print(f"📥 Fetched {len(square_items)} items from Square")
            
            changes = []
            updated_count = 0
            created_count = 0
            
            for item in square_items:
                # Detect changes
                change_snapshot = self._detect_changes(item)
                
                if change_snapshot:
                    changes.append(change_snapshot)
                    
                    if change_snapshot.change_type == 'create':
                        created_count += 1
                    elif change_snapshot.change_type == 'update':
                        updated_count += 1
                
                # Update cached item
                item['content_hash'] = self._calculate_hash(item)
                item['cached_at'] = datetime.now(timezone.utc)
                
                self.items_collection.replace_one(
                    {"id": item['id']},
                    item,
                    upsert=True
                )
            
            # Save change snapshots
            if changes:
                change_docs = [asdict(change) for change in changes]
                self.changes_collection.insert_many(change_docs)
            
            # Log sync operation
            sync_result = {
                "timestamp": sync_start,
                "total_items": len(square_items),
                "created_count": created_count,
                "updated_count": updated_count,
                "changes_detected": len(changes),
                "duration_seconds": (datetime.now(timezone.utc) - sync_start).total_seconds()
            }
            
            self.sync_log_collection.insert_one(sync_result)
            
            print(f"✅ Sync complete: {created_count} created, {updated_count} updated, {len(changes)} changes detected")
            
            return sync_result
            
        except Exception as e:
            error_result = {
                "timestamp": sync_start,
                "error": str(e),
                "status": "failed"
            }
            self.sync_log_collection.insert_one(error_result)
            raise
    
    def get_changed_items(self, since: Optional[datetime] = None) -> List[ChangeSnapshot]:
        """Get items that have changed since specified time"""
        query = {}
        if since:
            query["timestamp"] = {"$gte": since}
            
        change_docs = self.changes_collection.find(query).sort("timestamp", -1)
        
        changes = []
        for doc in change_docs:
            # Remove MongoDB's _id field and convert back to ChangeSnapshot
            if '_id' in doc:
                del doc['_id']
            doc['timestamp'] = doc['timestamp'].replace(tzinfo=timezone.utc)
            changes.append(ChangeSnapshot(**doc))
            
        return changes
    
    def get_item_history(self, item_id: str) -> List[ChangeSnapshot]:
        """Get change history for a specific item"""
        change_docs = self.changes_collection.find(
            {"item_id": item_id}
        ).sort("timestamp", -1)
        
        history = []
        for doc in change_docs:
            # Remove MongoDB's _id field and convert back to ChangeSnapshot
            if '_id' in doc:
                del doc['_id']
            doc['timestamp'] = doc['timestamp'].replace(tzinfo=timezone.utc)
            history.append(ChangeSnapshot(**doc))
            
        return history
    
    def get_cached_item(self, item_id: str) -> Optional[Dict]:
        """Get cached item by ID"""
        return self.items_collection.find_one({"id": item_id})
    
    def search_cached_items(self, name_pattern: str = None, sku_pattern: str = None, **filters) -> List[Dict]:
        """Search cached items with filters
        
        Args:
            name_pattern: Search by item name (regex)
            sku_pattern: Search by variation SKU (regex)
            **filters: Additional MongoDB query filters
        """
        query = {}
        
        if name_pattern and sku_pattern:
            # Search both name and SKU
            query["$or"] = [
                {"item_data.name": {"$regex": name_pattern, "$options": "i"}},
                {"item_data.variations.item_variation_data.sku": {"$regex": sku_pattern, "$options": "i"}}
            ]
        elif name_pattern:
            query["item_data.name"] = {"$regex": name_pattern, "$options": "i"}
        elif sku_pattern:
            query["item_data.variations.item_variation_data.sku"] = {"$regex": sku_pattern, "$options": "i"}
            
        for key, value in filters.items():
            query[key] = value
            
        return list(self.items_collection.find(query))
    
    def generate_change_report(self, since: Optional[datetime] = None) -> Dict:
        """Generate a detailed change report"""
        changes = self.get_changed_items(since)
        
        report = {
            "report_generated": datetime.now(timezone.utc),
            "since": since,
            "total_changes": len(changes),
            "summary": {
                "created": len([c for c in changes if c.change_type == 'create']),
                "updated": len([c for c in changes if c.change_type == 'update']),
                "deleted": len([c for c in changes if c.change_type == 'delete'])
            },
            "changes": []
        }
        
        for change in changes:
            change_info = {
                "item_id": change.item_id,
                "item_name": change.item_name,
                "change_type": change.change_type,
                "timestamp": change.timestamp,
                "version_change": f"{change.square_version_before} → {change.square_version_after}" if change.square_version_before else f"New → {change.square_version_after}"
            }
            
            if change.differences:
                change_info["key_changes"] = list(change.differences.keys())
                
            report["changes"].append(change_info)
            
        return report


def main():
    """CLI interface for the cache manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Square Items MongoDB Cache Manager")
    parser.add_argument("command", choices=["sync", "changes", "report", "item", "search"], 
                       help="Command to execute")
    parser.add_argument("--token", required=True, help="Square access token")
    parser.add_argument("--item-id", help="Item ID for item command")
    parser.add_argument("--name", help="Name pattern for search command")
    parser.add_argument("--sku", help="SKU pattern for search command")
    parser.add_argument("--since", help="Show changes since (YYYY-MM-DD)")
    parser.add_argument("--output", choices=["json", "table"], default="table",
                       help="Output format")
    
    args = parser.parse_args()
    
    # Initialize cache manager
    cache_manager = SquareCacheManager(args.token)
    
    try:
        if args.command == "sync":
            result = cache_manager.sync_from_square()
            print(json.dumps(result, indent=2, default=str))
            
        elif args.command == "changes":
            since = None
            if args.since:
                since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
                
            changes = cache_manager.get_changed_items(since)
            
            if args.output == "json":
                print(json.dumps([asdict(c) for c in changes], indent=2, default=str))
            else:
                print(f"\n📋 Found {len(changes)} changes:")
                print("=" * 80)
                for change in changes:
                    print(f"🔄 {change.item_name} ({change.item_id})")
                    print(f"   Type: {change.change_type}")
                    print(f"   Time: {change.timestamp}")
                    if change.differences:
                        print(f"   Changes: {', '.join(change.differences.keys())}")
                    print()
                    
        elif args.command == "report":
            since = None
            if args.since:
                since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
                
            report = cache_manager.generate_change_report(since)
            
            if args.output == "json":
                print(json.dumps(report, indent=2, default=str))
            else:
                print(f"\n📊 Change Report")
                print(f"Generated: {report['report_generated']}")
                print(f"Total changes: {report['total_changes']}")
                print(f"Created: {report['summary']['created']}, Updated: {report['summary']['updated']}, Deleted: {report['summary']['deleted']}")
                print("=" * 80)
                for change in report['changes'][:10]:  # Show first 10
                    print(f"🔄 {change['item_name']}")
                    print(f"   Type: {change['change_type']} | Version: {change['version_change']}")
                    print(f"   Time: {change['timestamp']}")
                    if 'key_changes' in change:
                        print(f"   Changes: {', '.join(change['key_changes'])}")
                    print()
                if len(report['changes']) > 10:
                    print(f"... and {len(report['changes']) - 10} more changes (use --output json for full report)")
            
        elif args.command == "item":
            if not args.item_id:
                print("Error: --item-id required for item command")
                sys.exit(1)
                
            item = cache_manager.get_cached_item(args.item_id)
            if item:
                print(json.dumps(item, indent=2, default=str))
            else:
                print(f"Item {args.item_id} not found in cache")
                
        elif args.command == "search":
            items = cache_manager.search_cached_items(name_pattern=args.name, sku_pattern=args.sku)
            
            if args.output == "json":
                print(json.dumps(items, indent=2, default=str))
            else:
                print(f"\n🔍 Found {len(items)} matching items:")
                print("=" * 80)
                for item in items:
                    name = item.get('item_data', {}).get('name', 'Unknown')
                    item_id = item.get('id', 'Unknown')
                    updated = item.get('updated_at', 'Unknown')
                    # Get SKU from first variation if available
                    sku = 'N/A'
                    variations = item.get('item_data', {}).get('variations', [])
                    if variations:
                        sku = variations[0].get('item_variation_data', {}).get('sku', 'N/A')
                    print(f"📦 {name}")
                    print(f"   ID: {item_id}")
                    print(f"   SKU: {sku}")
                    print(f"   Updated: {updated}")
                    print()
                    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()