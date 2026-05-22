"""Drive the PDP through the official MCP SDK via stdio.

This is the strongest end-to-end assurance that the wire shapes work.
Runs the FastMCP server in stdio mode in a subprocess and uses
the MCP client SDK to invoke tools.

Note: monkeypatching does not cross process boundaries.  The subprocess
inherits the container env so the DB is reachable, but the policy table
is empty in the test environment → libpbac would return NO_DECISION.
We call the read-only ``list_data_categories`` tool to exercise the
full transport stack without leaving committed rows in the shared DB.

Import note: tests/service/mcp/ is a local package whose __init__.py
shadows the top-level `mcp` SDK package when pytest adds tests/ to
sys.path.  We purge that shadow at module load time so the real SDK is
importable; the local package is restored to sys.modules afterwards so
other tests are unaffected.
"""

import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Fix import shadowing: tests/service/mcp/__init__.py shadows the real
# `mcp` SDK package when pytest prepends tests/ to sys.path.
# Remove any stale local-package entry so we get the site-packages version.
# ---------------------------------------------------------------------------
_stale = {k: v for k, v in sys.modules.items()
          if k == "mcp" and not getattr(v, "__file__", "").endswith("site-packages/mcp/__init__.py")}
for _k in _stale:
    del sys.modules[_k]

# Temporarily hide tests-tree entries from sys.path to force a clean import
# of the installed mcp package, then restore sys.path.
_hidden: list[str] = []
for _p in list(sys.path):
    if "tests" in _p and "site-packages" not in _p:
        sys.path.remove(_p)
        _hidden.append(_p)

try:
    import mcp.client.session  # noqa: E402 – runs at import time; that's intentional
    import mcp.client.stdio  # noqa: E402
finally:
    for _p in _hidden:
        if _p not in sys.path:
            sys.path.append(_p)

from mcp.client.session import ClientSession  # noqa: E402
from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: E402

# ---------------------------------------------------------------------------

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_pdp_stdio_lists_tools_and_calls_tool():
    """Spawn the server in stdio mode, verify tool list, call list_data_categories.

    We call the read-only ``list_data_categories`` tool rather than
    ``evaluate_policy`` so the test leaves no committed rows in the shared DB
    that would break the audit tests' ``.first()`` queries.
    """
    # Pass the full current-process env so the subprocess has the DB DSN,
    # FIDES__CONFIG_PATH, and all other Fides runtime config that
    # get_default_environment() omits.
    full_env = dict(os.environ)

    # The pytest env sets FIDES__TEST_MODE=true which routes DB connections to
    # a test-only DB name ("default_test_db") that may not exist in the
    # container.  The subprocess should connect to the normal dev DB instead.
    full_env["FIDES__TEST_MODE"] = "false"

    # When fides is installed in editable mode (pip install -e) the source
    # tree has no bin/ directory.  Resolve the library path explicitly so the
    # subprocess can find libpbac.so regardless of install mode.
    if "FIDES_PBAC_LIB_PATH" not in full_env:
        import sysconfig
        # Search site-packages locations for the wheel-installed bin/libpbac.so
        for site_dir in sysconfig.get_path("purelib"), sysconfig.get_path("platlib"):
            if site_dir is None:
                continue
            candidate = os.path.join(site_dir, "fides", "bin", "libpbac.so")
            if os.path.isfile(candidate):
                full_env["FIDES_PBAC_LIB_PATH"] = candidate
                break

    params = StdioServerParameters(
        command="python",
        args=["-m", "fides.api.mcp_pdp.server_stdio"],
        env=full_env,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Verify all expected PDP tools are registered.
            tools = await session.list_tools()
            tool_names = {t.name for t in tools.tools}
            assert "evaluate_policy" in tool_names
            assert "list_data_categories" in tool_names
            assert "list_data_uses" in tool_names
            assert "list_data_subjects" in tool_names
            assert "list_consumers" in tool_names
            assert "get_consumer" in tool_names
            assert "list_purposes" in tool_names
            assert "list_policies" in tool_names
            assert "set_session_purpose" in tool_names

            # Call a read-only tool end-to-end to prove the full transport
            # stack works: client → stdio → server → tool → response.
            result = await session.call_tool(
                "list_data_categories",
                arguments={},
            )
            assert result.content, "expected non-empty tool result"
            assert not getattr(result, "isError", False), (
                f"tool returned an error: {result.content!r}"
            )
            # FastMCP serialises a list-of-dicts return value as one content
            # item per dict.  We just need at least one category with a
            # ``fides_key`` field to confirm the tool ran successfully.
            import json
            first_payload = json.loads(result.content[0].text)
            assert "fides_key" in first_payload, (
                f"unexpected content: {result.content[0].text!r}"
            )
