#!/usr/bin/env python3
"""
Square Cache MCP Server

Exposes MongoDB-cached Square catalog operations as MCP tools for Claude Desktop.
"""

import json
import sys
import os
from typing import Any, Dict, List

# Add square-tools to path
sys.path.insert(0, os.path.expanduser('~/square-tools/cache-system'))

try:
    from square_cache_manager import SquareCacheManager
    from pymongo import MongoClient
except ImportError as e:
    print(f"Error: Missing dependencies - {e}", file=sys.stderr)
    sys.exit(1)


class SquareCacheMCP:
    """MCP Server for Square Cache operations"""
    
    def __init__(self):
        self.token = os.environ.get('SQUARE_TOKEN', '')
        
        # Always initialize MongoDB connection for read operations
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['square_cache']
        
        # Initialize cache manager if token available (for sync operations)
        if self.token:
            self.cache_manager = SquareCacheManager(self.token)
        else:
            self.cache_manager = None
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return list of available MCP tools"""
        return [
            {
                "name": "square_cache_search",
                "description": "Search cached Square catalog items by name or SKU. Returns instant results from MongoDB cache (100x faster than API).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name_pattern": {
                            "type": "string",
                            "description": "Search by item name (case-insensitive regex)"
                        },
                        "sku_pattern": {
                            "type": "string",
                            "description": "Search by SKU (case-insensitive regex)"
                        }
                    }
                }
            },
            {
                "name": "square_cache_get_item",
                "description": "Get complete cached item details by Square item ID. Returns full catalog data including variations, pricing, images, categories.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "item_id": {
                            "type": "string",
                            "description": "Square catalog item ID"
                        }
                    },
                    "required": ["item_id"]
                }
            },
            {
                "name": "square_cache_status",
                "description": "Get cache status including item count, last sync time, MongoDB health. Use to verify cache is operational.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "square_cache_changes",
                "description": "Get recent catalog changes with before/after snapshots. Shows what changed, when, and field-level diffs.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "since": {
                            "type": "string",
                            "description": "ISO date string (YYYY-MM-DD) to get changes since"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of changes to return (default: 20 if not specified)"
                        }
                    }
                }
            },
            {
                "name": "square_cache_sync",
                "description": "Trigger full catalog sync from Square API to MongoDB. Detects changes and creates audit snapshots. Requires SQUARE_TOKEN.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool invocation"""
        try:
            if tool_name == "square_cache_search":
                return self._search(arguments)
            elif tool_name == "square_cache_get_item":
                return self._get_item(arguments)
            elif tool_name == "square_cache_status":
                return self._status()
            elif tool_name == "square_cache_changes":
                return self._changes(arguments)
            elif tool_name == "square_cache_sync":
                return self._sync()
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}
    
    def _search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search cached items"""
        name_pattern = args.get('name_pattern')
        sku_pattern = args.get('sku_pattern')
        
        if not name_pattern and not sku_pattern:
            return {"error": "Either name_pattern or sku_pattern required"}
        
        if self.cache_manager:
            results = self.cache_manager.search_cached_items(
                name_pattern=name_pattern,
                sku_pattern=sku_pattern
            )
        else:
            # Direct MongoDB query for read-only access
            query = {}
            if name_pattern and sku_pattern:
                query["$or"] = [
                    {"item_data.name": {"$regex": name_pattern, "$options": "i"}},
                    {"item_data.variations.item_variation_data.sku": {"$regex": sku_pattern, "$options": "i"}}
                ]
            elif name_pattern:
                query["item_data.name"] = {"$regex": name_pattern, "$options": "i"}
            elif sku_pattern:
                query["item_data.variations.item_variation_data.sku"] = {"$regex": sku_pattern, "$options": "i"}
            
            results = list(self.db['catalog_items'].find(query))
        
        # Format results
        items = []
        for item in results:
            item.pop('_id', None)  # Remove MongoDB ID
            item.pop('content_hash', None)  # Internal field
            items.append({
                "id": item.get('id'),
                "name": item.get('item_data', {}).get('name'),
                "sku": self._get_sku(item),
                "price": self._get_price(item),
                "updated_at": item.get('updated_at')
            })
        
        return {
            "count": len(items),
            "items": items
        }
    
    def _get_item(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get item by ID"""
        item_id = args.get('item_id')
        if not item_id:
            return {"error": "item_id required"}
        
        if self.cache_manager:
            item = self.cache_manager.get_cached_item(item_id)
        else:
            item = self.db['catalog_items'].find_one({"id": item_id})
        
        if not item:
            return {"error": f"Item {item_id} not found in cache"}
        
        item.pop('_id', None)
        item.pop('content_hash', None)
        return {"item": item}
    
    def _status(self) -> Dict[str, Any]:
        """Get cache status"""
        try:
            # Test MongoDB connection
            self.client.admin.command('ismaster')
            mongodb_running = True
        except:
            mongodb_running = False
        
        items_count = self.db['catalog_items'].count_documents({})
        changes_count = self.db['change_snapshots'].count_documents({})
        syncs_count = self.db['sync_log'].count_documents({})
        
        last_sync = self.db['sync_log'].find_one({}, sort=[('timestamp', -1)])
        
        return {
            "mongodb_running": mongodb_running,
            "items_cached": items_count,
            "changes_tracked": changes_count,
            "sync_operations": syncs_count,
            "last_sync": {
                "timestamp": str(last_sync['timestamp']) if last_sync else None,
                "status": "success" if last_sync and not last_sync.get('error') else "error",
                "items_processed": last_sync.get('total_items', 0) if last_sync else 0
            } if last_sync else None
        }
    
    def _changes(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get recent changes"""
        since = args.get('since')
        limit = args.get('limit', 20)
        
        query = {}
        if since:
            from datetime import datetime
            since_date = datetime.fromisoformat(since)
            query['timestamp'] = {'$gte': since_date}
        
        changes = list(self.db['change_snapshots'].find(query).sort('timestamp', -1).limit(limit))
        
        results = []
        for change in changes:
            change.pop('_id', None)
            change.pop('before_data', None)  # Too large for MCP response
            change.pop('after_data', None)
            results.append({
                "item_id": change.get('item_id'),
                "item_name": change.get('item_name'),
                "change_type": change.get('change_type'),
                "timestamp": str(change.get('timestamp')),
                "differences": list(change.get('differences', {}).keys())
            })
        
        return {
            "count": len(results),
            "changes": results
        }
    
    def _sync(self) -> Dict[str, Any]:
        """Trigger cache sync"""
        if not self.cache_manager:
            return {"error": "Sync requires SQUARE_TOKEN environment variable"}
        
        try:
            result = self.cache_manager.sync_from_square()
            return {
                "success": True,
                "items_processed": result.get('total_items'),
                "changes_detected": result.get('changes_detected'),
                "created": result.get('created_count'),
                "updated": result.get('updated_count')
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_sku(self, item: Dict) -> str:
        """Extract SKU from first variation"""
        variations = item.get('item_data', {}).get('variations', [])
        if variations:
            return variations[0].get('item_variation_data', {}).get('sku', 'N/A')
        return 'N/A'
    
    def _get_price(self, item: Dict) -> str:
        """Extract price from first variation"""
        variations = item.get('item_data', {}).get('variations', [])
        if variations:
            price_money = variations[0].get('item_variation_data', {}).get('price_money', {})
            amount = price_money.get('amount', 0)
            currency = price_money.get('currency', 'USD')
            return f"${amount/100:.2f} {currency}"
        return 'N/A'


def main():
    """MCP server main loop with proper JSON-RPC 2.0 protocol"""
    server = SquareCacheMCP()
    
    # MCP stdio protocol (JSON-RPC 2.0)
    for line in sys.stdin:
        try:
            request = json.loads(line)
            request_id = request.get('id')
            method = request.get('method')
            
            if method == 'initialize':
                # MCP handshake
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "square-cache",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == 'tools/list':
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": server.get_tools()
                    }
                }
            elif method == 'tools/call':
                tool_name = request['params']['name']
                arguments = request['params'].get('arguments', {})
                tool_result = server.handle_tool_call(tool_name, arguments)
                
                # Check if tool returned error
                if "error" in tool_result:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32000,
                            "message": tool_result["error"]
                        }
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [{
                                "type": "text",
                                "text": json.dumps(tool_result, indent=2)
                            }]
                        }
                    }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            print(json.dumps(response))
            sys.stdout.flush()
            
        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get('id') if 'request' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == '__main__':
    main()
