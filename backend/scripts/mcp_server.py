"""
Run the Aztec List MCP server (stdio) for an MCP client like Claude Desktop.

    uv run python scripts/mcp_server.py

Exposes marketplace tools (search, semantic search, get listing, list categories)
backed by the app's services and database. Configure it in Claude Desktop; see
docs/08-mcp-server.md.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

# Make the `app` package importable when run as a standalone script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Load every ORM model so SQLAlchemy can resolve relationship() targets before queries.
importlib.import_module("app.api.v1.routes")

from app.mcp_server.server import mcp

if __name__ == "__main__":
    mcp.run()
