# Square Cache MCP Server - Warp Setup

Quick guide for adding square-cache MCP server to Warp.

## Prerequisites

1. **MongoDB running:**
   ```bash
   brew services start mongodb-community@8.0
   ```

2. **Python dependencies installed:**
   ```bash
   pip3 install pymongo requests
   ```

3. **Square token available:**
   ```bash
   echo $SQUARE_TOKEN  # or $SQUARE_ACCESS_TOKEN
   ```

## Add MCP Server to Warp

### Option 1: Via Warp Drive UI

1. Open Warp
2. Navigate to: **Warp Drive** → **Personal** → **MCP Servers**
3. Click **+ Add**
4. Select **CLI Server (Command)**
5. Paste this configuration:

```json
{
  "square-cache": {
    "command": "python3",
    "args": ["/Users/scottybe/square-tools/mcp-server/square_cache_mcp.py"],
    "env": {
      "SQUARE_TOKEN": "YOUR_SQUARE_TOKEN_HERE"
    }
  }
}
```

6. Replace `YOUR_SQUARE_TOKEN_HERE` with your actual token
7. Click **Add** then **Start**

### Option 2: Via Settings

1. Open Warp Settings: `Cmd + ,`
2. Go to: **AI** → **Manage MCP servers**
3. Follow same steps as Option 1

## Verify Setup

In Warp Agent Mode, try:

```
"What square-cache tools are available?"
```

You should see:
- square_cache_search
- square_cache_get_item
- square_cache_status
- square_cache_changes
- square_cache_sync

## Test the Tools

### Search by Name
```
"Search cache for Bears items"
```

### Search by SKU
```
"Check if SKU RG-0005 exists in cache"
```

### Get Item Details
```
"Get details for item A55Q4TG7EJ2IJUDIFX3VHVAH"
```

### Check Status
```
"What's the cache status? How many items?"
```

### View Changes
```
"What changed in the catalog today?"
```

### Sync Cache
```
"Sync the Square catalog cache"
```

## Troubleshooting

**Server won't start:**
- Check MongoDB: `brew services list | grep mongodb`
- Verify Python path: `which python3`
- Check logs: View Logs button in MCP Servers UI

**"Connection refused" errors:**
- Start MongoDB: `brew services start mongodb-community@8.0`
- Test connection: `mongosh square_cache --eval "db.catalog_items.countDocuments()"`

**"ModuleNotFoundError":**
- Install deps: `pip3 install pymongo requests`
- Check installed: `pip3 list | grep pymongo`

**Tools not appearing:**
- Verify server is **Started** (not just added)
- Restart Warp completely
- Check for error in View Logs

## Read-Only Mode

If you omit `SQUARE_TOKEN` from env:
- ✅ Search, get_item, status, changes work (MongoDB read-only)
- ❌ Sync requires token (needs Square API access)

## Security

- Token stored in Warp config (local only)
- MCP server runs locally (no network exposure)
- MongoDB localhost-only by default

## Integration with Skills

The square-cache skill (`~/skills/square-cache/SKILL.md`) documents both:
1. **Bash commands** - for terminal/Warp CLI use
2. **MCP tools** - for Warp Agent Mode use

Agent Mode will automatically use MCP tools when available.

## Related Files

- MCP Server: `~/square-tools/mcp-server/square_cache_mcp.py`
- Cache Manager: `~/square-tools/cache-system/square_cache_manager.py`
- CLI Wrapper: `~/square-tools/bin/square_cache.sh`
- Skill Doc: `~/skills/square-cache/SKILL.md`

## Commits

- MCP server implementation: `a4d2471`
- Critical bug fixes: `de3f200`
- Skills documentation: `9fe959e`
