"""Launch Diligence MCP server in stdio mode for Claude Desktop."""
from diligence.mcp.server import create_mcp_server
mcp = create_mcp_server(api_url="http://localhost:8000")
mcp.run(transport="stdio")
