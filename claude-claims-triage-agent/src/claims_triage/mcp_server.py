"""Exposes policy lookup over MCP so Claude Desktop or any MCP client can call it.

Run: python -m claims_triage.mcp_server
"""
from mcp.server.fastmcp import FastMCP

from .tools import PolicyLookup

mcp = FastMCP("claims-policy")
_lookup = PolicyLookup()


@mcp.tool()
def lookup_policy(policy_number: str) -> dict:
    """Return coverage details for a policy number, or an error if unknown."""
    p = _lookup.get(policy_number)
    return p.model_dump() if p else {"error": f"policy {policy_number} not found"}


if __name__ == "__main__":
    mcp.run()
