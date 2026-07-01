"""MCP server startup for the pip install path.

Starts FastMCP in a background thread so AI agents can connect
to the same machine running Diligence. Requires: pip install diligence[mcp]
"""
from __future__ import annotations

import threading
import logging

logger = logging.getLogger("diligence.mcp")


def start_mcp_background(api_url: str, api_token: str = "", port: int = 3001):
    """Start the MCP SSE server in a background thread.

    Args:
        api_url: Backend API base URL (e.g. http://localhost:8000)
        api_token: Bearer token for API auth
        port: Port for the MCP SSE server (default 3001)
    """
    try:
        from diligence.mcp.server import create_mcp_server
    except ImportError:
        logger.warning("MCP package not installed. Install with: pip install diligence[mcp]")
        return False

    def _run():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            mcp = create_mcp_server(api_url=api_url, api_token=api_token, port=port)
            mcp.run(transport="sse")
        except Exception as e:
            logger.error(f"MCP server failed: {e}")

    thread = threading.Thread(target=_run, daemon=True, name="mcp-server")
    thread.start()
    logger.info(f"MCP server starting on port {port}")
    return True
