# WARP.md

Context for Warp Agent Mode when working with this repo.

## What This Is

Square catalog management via MongoDB cache + MCP server for Claude Desktop.

**Stack:** Python/Bash, MongoDB, Square API  
**MCP Server:** For Claude Desktop only (Warp uses bash directly)

## Quick Commands

```bash
# Cache
square_cache.sh status
square_cache.sh sync
square_cache.sh search "query"
square_cache.sh search --sku RG-0005
square_cache.sh item ITEM_ID
square_cache.sh changes

# Photos (macOS only)
browse_photos.sh recent 10
photos_to_square.sh INDEX $SQUARE_TOKEN

# MongoDB direct
mongosh square_cache
```

## File Structure

```
bin/              # CLI scripts (square_cache.sh, photos_to_square.sh)
cache-system/     # Python: square_cache_manager.py, bg_removal_service.py
mcp-server/       # Claude Desktop MCP server
data/             # Exports, logs
```

## Setup

```bash
# One-time
brew install mongodb-community@8.0
brew services start mongodb-community@8.0
pip3 install pymongo requests Pillow

# Required
export SQUARE_TOKEN="token"

# Optional
export REMOVEBG_API_KEY="key"
export GEMINI_API_KEY="key"

# Init
source ~/Workspace/square-tools/config.sh
square_cache.sh sync
```

## MongoDB Schema

**Database:** `square_cache`

**Collections:**
- `catalog_items` - Cached Square items
- `change_snapshots` - Before/after diffs
- `sync_log` - Sync history  
- `bg_removal_cache` - Processed images

## Change Detection

SHA256 content hash (excludes `updated_at`, `version`) triggers:
- **create** - New item
- **update** - Modified item with field diffs
- **delete** - Removed item (not implemented)

## MCP Server

**For Claude Desktop only.** Config at `~/Library/Application Support/Claude/claude_desktop_config.json`

Tools: search, get_item, status, changes, sync

See `mcp-server/TROUBLESHOOTING.md` for fixes.

## Key Files

- `cache-system/square_cache_manager.py` - Core cache logic
- `bin/square_cache.sh` - CLI wrapper
- `mcp-server/square_cache_mcp.py` - Claude Desktop MCP server

## Troubleshooting

```bash
# MongoDB not running?
brew services start mongodb-community@8.0

# Check token
echo $SQUARE_TOKEN

# Test API
curl -H "Square-Version: 2024-09-18" \
     -H "Authorization: Bearer $SQUARE_TOKEN" \
     "https://connect.squareup.com/v2/catalog/list?types=ITEM&limit=1"

# Nuke cache
mongosh square_cache --eval "db.dropDatabase()"
square_cache.sh sync
```

## Docs

- `README.md` - Full system overview
- `IMAGE_PROCESSING.md` - AI background removal
- `mcp-server/` - Claude Desktop integration docs
