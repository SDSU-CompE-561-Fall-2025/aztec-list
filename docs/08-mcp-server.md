# MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io) server that exposes the marketplace
as tools, so an MCP client like Claude Desktop can browse Aztec List listings directly. It is a
thin layer: every tool reuses the existing service layer, so there is no duplicated business
logic (which also proves those services are cleanly factored).

## Tools

| Tool | Purpose |
| :--- | :--- |
| `list_categories` | List the marketplace categories. |
| `search_listings` | Keyword search with optional `category`, `min_price`, `max_price`, `condition`, `limit`. |
| `semantic_search_listings` | Meaning-based search (requires AI features enabled). |
| `get_listing` | Full details for one listing by id. |

## How it works

- `src/app/mcp_server/server.py` builds a `FastMCP` server and registers the tools. Each tool
  opens a session via the app's `SessionLocal`, calls `listing_service`, and returns serialized
  schema objects.
- `scripts/mcp_server.py` is the entry point: it puts `src` on the path, imports the app so all
  ORM models are registered, and runs the server over stdio.

## Run it (Claude Desktop)

Add this to your `claude_desktop_config.json` (use the absolute path to your `backend/`):

```json
{
  "mcpServers": {
    "aztec-list": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/aztec-list/backend",
        "python",
        "scripts/mcp_server.py"
      ]
    }
  }
}
```

Restart Claude Desktop, then ask it to use the Aztec List tools (for example, "search Aztec List
for a desk"). To try it locally with the MCP Inspector instead:

```bash
uv run --with "mcp[cli]" mcp dev scripts/mcp_server.py
```

## Caveats

- **Shared database.** The server reads the same database the app uses (`DB__DATABASE_URL`). Run
  the app at least once so the tables exist and there are listings to find.
- **Semantic search needs AI enabled.** `semantic_search_listings` requires `AI__ENABLED=true`.
  With AI off it falls back to keyword search. `search_listings`, `get_listing`, and
  `list_categories` work regardless.
- **Embedded Qdrant is single-process.** If the dev server is running with the default embedded
  on-disk Qdrant, a second process (this MCP server) cannot open the same `qdrant_data` for
  semantic search. Run Qdrant as a server (`VECTOR__QDRANT_URL`) to use semantic search from both
  at once. Keyword tools are unaffected.

## Testing

`tests/unit/test_mcp_server.py` calls the tools directly against the in-memory test database
(by pointing `SessionLocal` at the test session), covering keyword search, get-by-id, and the
category list.
