"""FastMCP server entry point.

Basic tools (Task 16 evaluate_policy, Task 18 discovery, Task 19 set_session_purpose)
register on import. The Fidesplus add-on `evaluate_with_inference` tool (Tasks
17-A and 17-B) registers itself at Fidesplus startup via the bootstrap module.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp_server = FastMCP("fides-mcp-pdp")


def get_sse_app():
    """Return an ASGI app exposing the FastMCP SSE transport."""
    return mcp_server.sse_app()


# Register tools.  Each import must happen after ``mcp_server`` is created so
# the decorator fires against the real instance.
from fides.api.mcp_pdp.tools.evaluate import evaluate_policy as _ep  # noqa: F401

mcp_server.tool()(_ep)

from fides.api.mcp_pdp.tools import discovery as _discovery  # noqa: F401, E402

for _fn in (
    _discovery.list_data_categories,
    _discovery.list_data_uses,
    _discovery.list_data_subjects,
    _discovery.list_consumers,
    _discovery.get_consumer,
    _discovery.list_purposes,
    _discovery.list_policies,
):
    mcp_server.tool()(_fn)
