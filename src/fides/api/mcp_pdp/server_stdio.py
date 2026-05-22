"""Stdio entry point for the PDP MCP server.

Run with: python -m fides.api.mcp_pdp.server_stdio
"""

from fides.api.mcp_pdp.server import mcp_server


def main() -> None:
    mcp_server.run(transport="stdio")


if __name__ == "__main__":
    main()
