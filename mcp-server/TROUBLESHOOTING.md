# MCP Server Troubleshooting

## "Server disconnected" Error in Claude Desktop

**Symptom:** Claude Desktop shows MCP server as "failed" with "Server disconnected" error.

**Root Cause:** Missing Python dependencies (`pymongo`, `requests`) in the Python interpreter used by Claude Desktop.

### Solution

Claude Desktop uses `/opt/homebrew/bin/python3` (Homebrew Python) which requires dependencies installed separately from your terminal Python.

**Install dependencies:**
```bash
/opt/homebrew/bin/pip3 install --break-system-packages pymongo requests
```

**Verify installation:**
```bash
/opt/homebrew/bin/python3 -c "import pymongo, requests; print('✅ OK')"
```

**Update config to use full path:**
```json
{
  "mcpServers": {
    "square-cache": {
      "command": "/opt/homebrew/bin/python3",
      "args": ["/Users/scottybe/workspace/square/square-tools/mcp-server/square_cache_mcp.py"],
      "env": {
        "SQUARE_ACCESS_TOKEN": "your_token"
      }
    }
  }
}
```

**Restart Claude Desktop** (Cmd+Q, then reopen)

### Why This Happens

- **Terminal Python:** May use pyenv, conda, or system Python with dependencies installed
- **Claude Desktop Python:** Uses Homebrew Python (`/opt/homebrew/bin/python3`) with separate packages
- **Solution:** Install dependencies for Homebrew Python specifically

### Testing the Fix

```bash
# Test MCP server with Claude Desktop's Python
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
  SQUARE_ACCESS_TOKEN=your_token \
  /opt/homebrew/bin/python3 ~/workspace/square/square-tools/mcp-server/square_cache_mcp.py
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

### Permission Denied

**Error:** "Permission denied" when executing script

**Solution:**
```bash
chmod +x ~/workspace/square/square-tools/mcp-server/square_cache_mcp.py
```

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
