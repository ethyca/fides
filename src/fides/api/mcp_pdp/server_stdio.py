"""Stdio entry point for the PDP MCP server.

Run with: python -m fides.api.mcp_pdp.server_stdio

If the optional Fidesplus add-ons package is installed in the same Python
environment, its tools (e.g. evaluate_with_inference) are registered on the
shared FastMCP server before stdio mode starts. Without Fidesplus, only the
Fides OSS PDP tools are exposed.
"""

from loguru import logger

from fides.api.mcp_pdp.server import mcp_server


def _try_register_fidesplus_addons() -> None:
    try:
        from fidesplus.mcp_pdp_addons.bootstrap import (
            register_pdp_addons,
        )
    except ImportError:
        return
    register_pdp_addons()
    logger.info("Fidesplus MCP PDP add-ons registered on stdio server")


def main() -> None:
    _try_register_fidesplus_addons()
    mcp_server.run(transport="stdio")


if __name__ == "__main__":
    main()
