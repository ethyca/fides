"""Stdio entry point for the PDP MCP server.

Run with: python -m fides.api.mcp_pdp.server_stdio

If the optional Fidesplus add-ons package is installed in the same Python
environment, its tools (e.g. evaluate_with_inference) are registered on the
shared FastMCP server before stdio mode starts. Without Fidesplus, only the
Fides OSS PDP tools are exposed.

stdio MCP protocol uses stdout exclusively for JSON-RPC frames. Any other
process writing to stdout corrupts the stream. We mitigate by:
  - silencing LiteLLM's debug/info output before any inference runs
  - configuring Python's logging to use stderr
  - redirecting unexpected stdout writes (from libraries that ignore the
    above) to stderr via a saved-and-restored sys.stdout pointer
"""

import logging
import os
import sys

from loguru import logger

from fides.api.mcp_pdp.server import mcp_server


def _silence_stdout_chatter() -> None:
    """Push noisy library output to stderr before the stdio server starts."""
    # LiteLLM (used by Fidesplus inference add-on)
    try:
        import litellm

        litellm.suppress_debug_info = True
        litellm.set_verbose = False
        os.environ.setdefault("LITELLM_LOG", "ERROR")
    except ImportError:
        pass

    # Python stdlib logging - force stderr regardless of any prior configuration
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        if isinstance(handler, logging.StreamHandler) and handler.stream is sys.stdout:
            handler.stream = sys.stderr
    logging.basicConfig(stream=sys.stderr, force=True)


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
    _silence_stdout_chatter()
    _try_register_fidesplus_addons()
    mcp_server.run(transport="stdio")


if __name__ == "__main__":
    main()
