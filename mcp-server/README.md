# Square Cache MCP Server

MCP server for Claude Desktop to access Square catalog cache.

**For Claude Desktop only.** Warp Agent uses bash commands (`square_cache.sh`).

This server is intended to run **alongside** the official Square MCP server:
- Official Square MCP (`mcp_square_api`) for direct API calls
- This local `square_cache_mcp` MCP for fast Mongo-backed lookups and change history

## 5 Tools Exposed

1. **search** - Search by name/SKU
2. **get_item** - Get full item details
3. **status** - Cache health check
4. **changes** - View recent changes
5. **sync** - Trigger catalog sync

## Setup

**1. Install uv/uvx:**
```bash
uv --version
uvx --version
```

**2. Configure Claude Desktop:**

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

This launcher script sources `/Users/scottybe/.config/claude-mcp/.env`, so secrets stay out of the JSON config.

**3. Restart Claude Desktop** (Cmd+Q, reopen)

**4. Test:** "What square_cache_mcp tools are available?"

## Usage Examples

```
"Search cache for Bears items"
"Check if SKU RG-0005 exists"
"Get details for item A55Q4TG7EJ2IJUDIFX3VHVAH"
"What changed in the catalog today?"
"Check cache status"
```

## Troubleshooting

See `TROUBLESHOOTING.md` for:
- "Server disconnected" error (missing dependencies)
- Zod validation errors (fixed in commit 3cdd82c)
- MongoDB connection issues
- Other common problems

## How It Works

Claude Desktop → MCP server → MongoDB → Structured JSON → Natural language response

No bash/terminal needed - Claude calls tools directly.

## Files

- `square_cache_mcp.py` - MCP server (380 lines)
- `README.md` - This file
- `TROUBLESHOOTING.md` - Fix common issues
- `MCP_RATIONALE.md` - Why MCP vs bash
- `SESSION_SUMMARY.md` - Implementation history
