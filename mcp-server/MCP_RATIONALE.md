# MCP Server Implementation Rationale

## The Problem

**Original Issue:** Claude Desktop (the chat application) cannot execute bash commands or access local files directly. This created a workflow bottleneck:

1. User asks Claude Desktop: "Search cache for Bears items"
2. Claude Desktop responds: "Run this command: `square_cache.sh search Bears`"
3. User copies command, runs in terminal, copies output back
4. Claude Desktop interprets the pasted output
5. Repeat for each cache operation

**Pain Points:**
- Manual copy/paste required for every cache query
- Breaks conversational flow
- Error-prone (typos, paste errors)
- No direct tool integration
- Claude Desktop can't autonomously query cache

## The Solution: MCP Server

**MCP (Model Context Protocol)** allows Claude Desktop to call local tools as if they were native APIs.

### What We Built

A Python-based MCP server (`square_cache_mcp.py`) that:
- Connects directly to MongoDB (localhost:27017)
- Exposes 5 cache operations as MCP tools
- Implements JSON-RPC 2.0 protocol
- Handles authentication via `SQUARE_ACCESS_TOKEN` (with legacy `SQUARE_TOKEN` fallback)
- Returns structured JSON responses

### Architecture

```
Claude Desktop
    ↓ (MCP JSON-RPC)
square_cache_mcp.py
    ↓ (MongoDB driver)
MongoDB (square_cache database)
    ↓ (Square API sync)
Square Catalog API
```

**No bash commands involved** - Claude Desktop calls Python MCP server directly.

## Why Not Just Give Claude Desktop Bash Access?

**Security & Design:** Claude Desktop is sandboxed and cannot execute arbitrary shell commands by design. This is intentional security.

**MCP Benefits:**
- ✅ Structured tool interface (defined schemas)
- ✅ Type-safe parameters
- ✅ Error handling built-in
- ✅ Scoped permissions (only cache operations)
- ✅ No arbitrary command execution
- ✅ Portable across environments

## Comparison: Warp Agent vs Claude Desktop

### Warp Agent (this conversation)
- **Environment:** Warp terminal with Agent Mode
- **Access:** Direct bash command execution via `run_shell_command`
- **Usage:** Can run `square_cache.sh` scripts directly
- **Limitation:** Only available in Warp terminal sessions

### Claude Desktop
- **Environment:** Standalone chat application
- **Access:** MCP tools only (no bash)
- **Usage:** Calls `square_cache_search`, `square_cache_status`, etc.
- **Benefit:** Works from any conversation, no terminal needed

## Tools Exposed via MCP

| Tool | Purpose | Parameters |
|------|---------|------------|
| `square_cache_search` | Search by name or SKU | name_pattern, sku_pattern |
| `square_cache_get_item` | Get full item details | item_id |
| `square_cache_status` | Check cache health | (none) |
| `square_cache_changes` | View recent changes | since, limit |
| `square_cache_sync` | Trigger full sync | (none) |

## Implementation Details

### JSON-RPC 2.0 Compliance

**Before (broken):**
```json
{"tools": [...]}
```

**After (correct):**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [...]
  }
}
```

### Critical Bug Fixes

**Issue 1: Missing `self.client`**
- Problem: MongoDB client only initialized when token absent
- Fix: Always initialize `self.client` and `self.db` for read operations
- Impact: `square_cache_status` now works with token present

**Issue 2: Protocol Non-compliance**
- Problem: Missing `initialize` handshake, improper error codes
- Fix: Added JSON-RPC 2.0 wrappers, error codes (-32700, -32601, -32603)
- Impact: Claude Desktop can now properly negotiate with server

## Configuration

**Claude Desktop:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mcp_square_api": {
      "command": "npx",
      "args": ["mcp-remote", "https://mcp.squareup.com/sse"]
    },
    "square_cache_mcp": {
      "command": "/Users/scottybe/.config/claude-mcp/bin/start-square-cache-mcp.sh",
      "args": []
    }
  }
}
```

**Warp Agent:** Not needed - uses bash commands directly via `run_shell_command`

## Testing

### Command-Line Testing

```bash
# Test tools/list
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 square_cache_mcp.py

# Test status
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"square_cache_status","arguments":{}}}' | python3 square_cache_mcp.py

# Test search
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"square_cache_search","arguments":{"sku_pattern":"RG-0005"}}}' | python3 square_cache_mcp.py
```

### Expected Claude Desktop Usage

**Natural language queries:**
- "What square_cache_mcp tools are available?"
- "Check the cache status"
- "Search cache for Bears items"
- "Get details for item A55Q4TG7EJ2IJUDIFX3VHVAH"
- "What changed in the catalog today?"

**Claude Desktop will:**
1. Recognize these as cache queries
2. Call appropriate MCP tool
3. Parse structured JSON response
4. Present results naturally in conversation

## Benefits Achieved

### For User
- ✅ No more copy/paste workflow
- ✅ Conversational cache queries
- ✅ Faster iteration
- ✅ Works from any Claude Desktop chat

### For Claude Desktop
- ✅ Direct cache access
- ✅ Structured tool interface
- ✅ Type-safe parameters
- ✅ Autonomous cache queries

### For System
- ✅ Consistent with MCP standards
- ✅ Secure (scoped permissions)
- ✅ Maintainable (single MCP server vs multiple bash scripts)
- ✅ Extensible (easy to add new tools)

## Future Enhancements

### Potential Additional Tools
- `square_cache_find_duplicates` - Find items with duplicate SKUs
- `square_cache_validate` - Check for data integrity issues
- `square_cache_export` - Export cache data to CSV/JSON
- `square_cache_stats` - Aggregate statistics and reports

### Integration Opportunities
- Add MCP tools for `square-image-upload` skill
- Add MCP tools for `product-labeler` skill
- Create unified Richmond General MCP server with all tools

## References

- **MCP Protocol:** https://modelcontextprotocol.io
- **JSON-RPC 2.0:** https://www.jsonrpc.org/specification
- **Implementation:** `~/square-tools/mcp-server/square_cache_mcp.py`
- **Setup Guide:** `~/square-tools/mcp-server/WARP_SETUP.md`
- **Skills Doc:** `~/skills/square-cache/SKILL.md`

## Commits

- `a4d2471` - Initial MCP server implementation
- `de3f200` - Critical bug fixes (self.client + JSON-RPC 2.0)
- `0d3cdec` - Warp-specific setup documentation
- `[TBD]` - Claude Desktop configuration automation

## Related Linear Issues

- TVM-29: Integrate square-cache with rg-inventory (completed)
- TVM-30: Document square-cache skill (completed)
- TVM-31: MCP server implementation (this document)
