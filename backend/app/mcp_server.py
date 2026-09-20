"""Optional standards-compliant MCP server. Run after installing `mcp` extra."""
from app.services.mcp_tool_service import TOOL_DEFINITIONS
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("LabTrace")
    @mcp.tool()
    def list_labtrace_tools() -> list[dict]:
        """Discover LabTrace tools. Authenticated tool invocation is hosted by the app boundary."""
        return TOOL_DEFINITIONS
except ImportError:
    mcp = None

if __name__ == "__main__":
    if mcp is None: raise SystemExit("Install the optional 'mcp' package to run the MCP server")
    mcp.run()
