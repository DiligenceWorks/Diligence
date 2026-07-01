"""Agent connection endpoint — returns MCP config for AI agent setup."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from diligence.config import get_settings
from diligence.utils.auth import get_current_user

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.get("/config")
async def agent_config(user=Depends(get_current_user)):
    """Return MCP connection details for the authenticated user."""
    settings = get_settings()

    # Determine MCP URL based on deployment mode
    base = settings.base_url.rstrip("/")
    if settings.is_sqlite:
        # pip install path — MCP served from same process
        mcp_url = f"{base}/mcp/sse"
    else:
        # Docker path — MCP on separate container port 3001
        from urllib.parse import urlparse
        parsed = urlparse(base)
        docker_host = parsed.hostname or "localhost"
        mcp_url = f"http://{docker_host}:3001/sse"

    return {
        "mcp_url": mcp_url,
        "api_token": settings.api_token if getattr(user, "is_admin", False) else None,
        "api_token_set": bool(settings.api_token),
        "deployment": "local" if settings.is_sqlite else "docker",
        "base_url": base,
        "tools_count": 14,
    }
