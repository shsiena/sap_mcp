from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from system_prompt import SYSTEM_PROMPT

# import plain functions
from tools.metadata_tools import (
    load_sap_metadata as _load_sap_metadata,
    get_sales_order_metadata as _get_sales_order_metadata,
)

from tools.query_tools import query_sales_orders as _query_sales_orders
# from tools.auth_tools import set_sap_credentials as _set_sap_credentials  # if you use it

load_dotenv()

mcp = FastMCP("sap-sd-server")


@mcp.prompt()
def system(ctx, message: str):
    return SYSTEM_PROMPT


# Now wrap the imported functions with MCP tools:

@mcp.tool()
def load_sap_metadata() -> str:
    return _load_sap_metadata()


@mcp.tool()
def get_sales_order_metadata() -> dict:
    return _get_sales_order_metadata()


@mcp.tool()
def query_sales_orders(entity_set: str, filter: str = "", select: str = "", top: int = 20) -> dict:
    return _query_sales_orders(entity_set, filter, select, top)


# If you keep auth tool:
# @mcp.tool()
# def set_sap_credentials(username: str, password: str, metadata_url: str) -> str:
#     return _set_sap_credentials(username, password, metadata_url)

@app.get("/sse")
async def sse():
    return sse_client(url="http://localhost:8002/sse")


if __name__ == "__main__":
    mcp.run(transport="sse")
