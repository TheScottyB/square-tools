# Tool Surface Matrix

Authoritative capability mapping for Square tooling.

## Runtime Modes

- `WEB_SAFE`: no local filesystem/photos/chrome injection operations.
- `LOCAL_STANDARD`: local tooling + network, no Photos and no JS injection.
- `LOCAL_PRIVILEGED`: full local/Photos/Chrome/injection operations.

## User CLI Tools

| Command Surface | Required Mode | Required Capabilities | Notes |
|---|---|---|---|
| `square_cache.sh status` | `WEB_SAFE` | `mcp_local_tools` | Local Mongo cache health/read check |
| `square_cache.sh search` | `WEB_SAFE` | `mcp_local_tools` | Catalog read/search |
| `square_cache.sh changes` | `WEB_SAFE` | `mcp_local_tools` | Change-history read |
| `square_cache.sh report` | `WEB_SAFE` | `mcp_local_tools` | Read-only reporting |
| `square_cache.sh item` | `WEB_SAFE` | `mcp_local_tools` | Read single cached item |
| `square_cache.sh sync` | `LOCAL_STANDARD` | `mcp_local_tools`, `network_access` | Cache mutation + Square API call |
| `browse_photos.sh` | `LOCAL_PRIVILEGED` | `filesystem_full_access`, `photos_full_access` | macOS Photos access |
| `photos_to_square.sh` | `LOCAL_PRIVILEGED` | `filesystem_full_access`, `photos_full_access`, `network_access` | Photos export + upload |
| `process_and_upload.sh` | `LOCAL_PRIVILEGED` | `filesystem_full_access`, `photos_full_access`, `network_access` | Photos export + AI processing + upload |

## MCP Tools (`square_cache_mcp`)

| MCP Tool | Required Mode | Required Capabilities | Notes |
|---|---|---|---|
| `square_cache_search` | `WEB_SAFE` | `mcp_local_tools` | Read-only cache search |
| `square_cache_get_item` | `WEB_SAFE` | `mcp_local_tools` | Read-only item details |
| `square_cache_status` | `WEB_SAFE` | `mcp_local_tools` | Read-only status |
| `square_cache_changes` | `WEB_SAFE` | `mcp_local_tools` | Read-only change history |
| `square_cache_sync` | `LOCAL_STANDARD` | `mcp_local_tools`, `network_access` | Mutating cache sync |

## Extension Scripting Operations

| Operation | Required Mode | Required Capabilities | Notes |
|---|---|---|---|
| `chrome_execute_script` | `LOCAL_PRIVILEGED` | `chrome_control`, `js_injection` | Action-based JS execution |
| `chrome_insert_css` | `LOCAL_STANDARD` | `chrome_control` | CSS-only injection |

## Enforcement

- Contract files: `runtime/capability_matrix.json`, `runtime/runtime_profiles.json`, `runtime/operation_policy.json`
- Gate script: `bin/agent_preflight.sh`
- Expected entrypoint contract:

```bash
agent_preflight.sh --operation <op> --mode <mode> --runtime <id>
```
