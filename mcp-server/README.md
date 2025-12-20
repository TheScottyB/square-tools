# Square Cache MCP Server

MCP (Model Context Protocol) server that exposes Square catalog cache operations to Claude Desktop.

## What This Enables

Claude Desktop can directly:
- ✅ Search cached items by name or SKU
- ✅ Get item details instantly (no API calls)
- ✅ Check cache status
- ✅ View recent catalog changes
- ✅ Trigger cache sync

No need to copy/paste terminal commands - Claude calls these as native tools!

## Setup for Claude Desktop

### 1. Install Dependencies

```bash
pip3 install pymongo requests
```

### 2. Add to Claude Desktop Config

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this server configuration:

```json
{
  "mcpServers": {
    "square-cache": {
      "command": "python3",
      "args": ["/Users/scottybe/square-tools/mcp-server/square_cache_mcp.py"],
      "env": {
        "SQUARE_TOKEN": "YOUR_SQUARE_TOKEN_HERE"
      }
    }
  }
}
```

**Note:** Replace `YOUR_SQUARE_TOKEN_HERE` with your actual Square API token.

### 3. Restart Claude Desktop

Close and reopen Claude Desktop app for changes to take effect.

### 4. Verify in Claude Desktop

Ask Claude: "What square-cache tools are available?"

You should see 5 tools listed:
- `square_cache_search`
- `square_cache_get_item`
- `square_cache_status`
- `square_cache_changes`
- `square_cache_sync`

## Available Tools

### square_cache_search

Search catalog by name or SKU.

**Parameters:**
- `name_pattern` (optional): Search by item name
- `sku_pattern` (optional): Search by SKU

**Example usage in Claude:**
```
"Search cache for items named Bears"
"Check if SKU RG-0010 exists"
"Find items with RG- prefix"
```

### square_cache_get_item

Get complete item details by ID.

**Parameters:**
- `item_id` (required): Square catalog item ID

**Example usage:**
```
"Get details for item A55Q4TG7EJ2IJUDIFX3VHVAH"
"Show me the full catalog data for that Bears button"
```

### square_cache_status

Check cache health and statistics.

**Example usage:**
```
"Check cache status"
"How many items are cached?"
"When was the last sync?"
```

### square_cache_changes

View recent catalog changes.

**Parameters:**
- `since` (optional): ISO date string (YYYY-MM-DD)
- `limit` (optional): Max results (default 20)

**Example usage:**
```
"What changed in the catalog today?"
"Show changes since December 1st"
"What are the last 10 catalog changes?"
```

### square_cache_sync

Trigger full catalog sync.

**Example usage:**
```
"Sync the cache from Square"
"Update the catalog cache"
```

## How It Works

1. **Claude Desktop** loads MCP server on startup
2. **MCP server** connects to your local MongoDB (localhost:27017)
3. **Claude** calls tools natively (no bash/terminal required)
4. **MCP server** queries MongoDB and returns structured JSON
5. **Claude** interprets results and responds naturally

## Read-Only Mode

If `SQUARE_TOKEN` is not set in config:
- ✅ Search, get_item, status, changes all work (read-only MongoDB access)
- ❌ Sync requires token (needs Square API access)

## Troubleshooting

**"Connection refused" errors:**
- Ensure MongoDB is running: `brew services start mongodb-community@8.0`
- Test connection: `mongosh square_cache --eval "db.catalog_items.countDocuments()"`

**"ModuleNotFoundError":**
- Install dependencies: `pip3 install pymongo requests`
- Check Python path matches config

**Tools not appearing in Claude:**
- Verify config file syntax (valid JSON)
- Restart Claude Desktop completely
- Check Claude Desktop logs for MCP errors

**"Item not found" responses:**
- Run initial sync: `~/square-tools/bin/square_cache.sh sync`
- Verify MongoDB has data: `mongosh square_cache`

## Integration with Skills

The square-cache skill (`~/skills/square-cache/SKILL.md`) now references both:
1. **Bash commands** for terminal/Warp usage
2. **MCP tools** for Claude Desktop usage

Claude will automatically use the appropriate method based on context.

## Security Notes

- Token stored in Claude Desktop config (local file, not shared)
- MCP server runs locally (no network exposure)
- MongoDB connection is localhost-only by default
- Read-only mode available without token

## Files

- `square_cache_mcp.py` - MCP server implementation
- `README.md` - This file

## Related Documentation

- Square Cache Skill: `~/skills/square-cache/SKILL.md`
- Cache Manager: `~/square-tools/cache-system/square_cache_manager.py`
- CLI Wrapper: `~/square-tools/bin/square_cache.sh`
