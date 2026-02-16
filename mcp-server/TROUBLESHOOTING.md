# MCP Server Troubleshooting

## "Server disconnected" Error in Claude Desktop

**Symptom:** Claude Desktop shows MCP server as "failed" with "Server disconnected" error.

**Root Cause:** Local MCP package cannot start or dependencies cannot resolve in the runtime.

### Solution

This server is launched via `uvx` from the local `mcp-server` directory.

**Verify uvx is installed:**
```bash
uv --version
uvx --version
```

**Verify the local package starts:**
```bash
uvx --from ~/workspace/square/square-tools/mcp-server square-cache-mcp
```

**Update config to use uvx:**
```json
{
  "mcpServers": {
    "square_cache_mcp": {
      "command": "/Users/scottybe/.config/claude-mcp/bin/start-square-cache-mcp.sh",
      "args": []
    }
  }
}
```

The launcher script sources `/Users/scottybe/.config/claude-mcp/.env` and executes `uvx --from ... square-cache-mcp`.

**Restart Claude Desktop** (Cmd+Q, then reopen)

### Why This Happens

- `uvx` missing or not on PATH
- Local package metadata missing/invalid
- Environment variables missing for sync operations

### Testing the Fix

```bash
# Test MCP server with uvx package runtime
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
  SQUARE_ACCESS_TOKEN=your_token \
  SQUARE_TOKEN=your_token \
  SQUARE_CACHE_SYSTEM_PATH=~/workspace/square/square-tools/cache-system \
  uvx --from ~/workspace/square/square-tools/mcp-server square-cache-mcp
```

Should return JSON with 5 tools listed.

## Zod Validation Errors

**Symptom:** Error message with "invalid_union", "Expected string, received null", "ZodError" in Claude Desktop logs.

**Root Cause:** inputSchema contains fields Claude Desktop doesn't support (like `default`).

**Solution:** This was fixed in commit `3cdd82c`. Update your MCP server:

```bash
cd ~/workspace/square/square-tools
git pull origin main
```

Restart Claude Desktop.

**Why:** Claude Desktop uses Zod for validation and doesn't support JSON Schema's `default` keyword in inputSchema.

## Other Common Issues

### MongoDB Not Running

**Error:** "Connection refused" in logs

**Solution:**
```bash
brew services start mongodb-community@8.0
```

### Wrong Token

**Error:** "Sync requires SQUARE_ACCESS_TOKEN" for read-only operations

**Solution:** Token is optional for search/status/changes. Only sync needs token.

### Package/Build Errors

**Error:** Build/install failure from `uvx --from ...`

**Solution:** Ensure `~/workspace/square/square-tools/mcp-server/pyproject.toml` exists and includes required dependencies (`pymongo`, `requests`).

### Port Already in Use

**Error:** MongoDB can't start (port 27017 in use)

**Solution:**
```bash
# Find process using port
lsof -i :27017

# Kill if needed
kill -9 <PID>

# Restart MongoDB
brew services restart mongodb-community@8.0
```

## Logs Location

Claude Desktop logs are in:
- `~/Library/Logs/Claude/mcp*.log`

View with:
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

## Still Not Working?

1. Check Claude Desktop logs
2. Test MCP server directly (command above)
3. Verify MongoDB is running: `mongosh square_cache --eval "db.catalog_items.countDocuments()"`
4. Check config syntax: `cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq`
