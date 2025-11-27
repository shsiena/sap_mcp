from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from system_prompt import SYSTEM_PROMPT

# Billing-related functions
from tools.metadata_tools import (
    load_billing_metadata as _load_billing_metadata,
    get_billing_document_metadata as _get_billing_document_metadata,
)

from tools.query_tools import (
    query_billing_documents as _query_billing_documents,
)

load_dotenv()

mcp = FastMCP("sap-billing-server")


@mcp.prompt()
def system(ctx, message: str):
    return SYSTEM_PROMPT


# ─────────────────────────────────────────────
# Billing Document Tool Wrappers
# ─────────────────────────────────────────────

@mcp.tool()
def load_billing_metadata() -> str:
    """Loads SAP Billing Document metadata from the OData service."""
    return _load_billing_metadata()


@mcp.tool()
def get_billing_document_metadata() -> dict:
    """Returns parsed metadata (fields, associations, types) for billing docs."""
    return _get_billing_document_metadata()


@mcp.tool()
def query_billing_documents(entity_set: str, filter: str = "",
                            select: str = "", top: int = 20) -> dict:
    """Queries Billing Document OData entities using filters, select, top."""
    return _query_billing_documents(entity_set, filter, select, top)


# ─────────────────────────────────────────────

mcp.run()
