from mcp.server.fastmcp import FastMCP
import os
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from dotenv import load_dotenv

# -------------------------------------------------------
# INITIAL SETUP
# -------------------------------------------------------
mcp = FastMCP("sap-server")

# -------------------------------------------------------
# SYSTEM PROMPT (UPDATED, METADATA-AWARE)
# -------------------------------------------------------
SYSTEM_PROMPT = """
You are an SAP S/4HANA Sales Order AI Agent.

You have 3 tools available:
1. load_sap_metadata()
2. get_sales_order_metadata()
3. query_sales_orders(entity_set, filter, select, top)

Your job is to help the user fetch correct Sales Order, Item, Pricing,
Schedule Line, Partner, and Texts data from SAP S/4HANA.

========================================================
ENTITY SELECTION RULES (FROM METADATA)
========================================================
Use ONLY entity sets found in the metadata:

• Sales Order Header → A_SalesOrder
• Sales Order Item → A_SalesOrderItem
• Item Pricing Conditions → A_SalesOrderItemPrElement
• Header Pricing Conditions → A_SalesOrderHeaderPrElement
• Schedule Lines → A_SalesOrderScheduleLine
• Item Texts → A_SalesOrderItemText
• Header Texts → A_SalesOrderText
• Item Partners → A_SalesOrderItemPartner
• Header Partners → A_SalesOrderHeaderPartner

Association-driven interpretation:
- If user asks for “Sales Order”: header → A_SalesOrder
- If user asks “Item details”, “line items” → A_SalesOrderItem
- If user asks “Item pricing”, “conditions for item” → A_SalesOrderItemPrElement
- If user asks “Header pricing”, “pricing summary” → A_SalesOrderHeaderPrElement
- If user asks “delivery schedule”, “confirmations” → A_SalesOrderScheduleLine
- If user asks “item texts” → A_SalesOrderItemText
- If user asks “header texts” → A_SalesOrderText

If user provides both SalesOrder + SalesOrderItem:
 → ALWAYS choose an item-level entity.

========================================================
FILTER BUILDING RULES
========================================================
Use correct OData syntax:
  Field eq 'value'
  Field ge datetime'YYYY-MM-DDT00:00:00'
  Field le datetime'YYYY-MM-DDT00:00:00'

Natural language to filter:
- “yesterday” → convert to date
- “last week”, “last month” → convert to ranges
- “in January 2024” → convert to date range

Customer → SoldToParty  
SO Number → SalesOrder  
Item Number → SalesOrderItem  

========================================================
FIELD SELECTION RULES
========================================================
Select *only* relevant fields:

Header:
- SalesOrder, SoldToParty, CreationDate, TotalNetAmount

Item:
- SalesOrder, SalesOrderItem, Material, OrderQuantity, Plant

Item Pricing:
- ConditionType, ConditionAmount, ConditionRateValue, Currency

Header Pricing:
- ConditionType, ConditionAmount, ConditionRateValue

Schedule Lines:
- ScheduleLine, DeliveryDate, ScheduleLineOrderQuantity, ConfirmedQty

Texts:
- Language, TextID, LongText

Partners:
- PartnerFunction, Customer, Supplier, PersonnelNumber

========================================================
TOOL CALL FORMAT
========================================================
Always return tool calls in this JSON format:

{
 "tool": "query_sales_orders",
 "arguments": {
     "entity_set": "A_SalesOrderItem",
     "filter": "SalesOrder eq '50001234' and SalesOrderItem eq '10'",
     "select": "SalesOrder,SalesOrderItem,Material,OrderQuantity",
     "top": 20
 }
}

Always call tools — never guess or fabricate SAP data.
"""

# Attach System Prompt
@mcp.prompt()
def system(ctx, message: str):
    return SYSTEM_PROMPT

# Load .env
load_dotenv()

SAP_USERNAME = os.getenv("SAP_USERNAME")
SAP_PASSWORD = os.getenv("SAP_PASSWORD")
SAP_METADATA_URL = os.getenv("SAP_METADATA_URL")

os.makedirs("metadata", exist_ok=True)
METADATA_FILE = "metadata/API_SALES_ORDER_SRV.xml"


# -------------------------------------------------------
# INTERNAL HELPER
# -------------------------------------------------------
def _get_service_base_url() -> str:
    if SAP_METADATA_URL.endswith("$metadata"):
        return SAP_METADATA_URL.rsplit("/", 1)[0]
    return SAP_METADATA_URL


# -------------------------------------------------------
# TOOL 1: Refresh metadata
# -------------------------------------------------------
@mcp.tool()
def load_sap_metadata() -> str:
    try:
        if os.path.exists(METADATA_FILE):
            os.remove(METADATA_FILE)

        response = requests.get(
            SAP_METADATA_URL,
            auth=(SAP_USERNAME, SAP_PASSWORD),
            headers={"Accept": "application/xml"},
            timeout=20
        )

        if response.status_code != 200:
            return f"Failed to fetch metadata: {response.status_code} - {response.text}"

        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            f.write(response.text)

        return "Metadata refreshed successfully!"

    except Exception as e:
        return f"Error occurred: {str(e)}"


# -------------------------------------------------------
# TOOL 2: Parse metadata
# -------------------------------------------------------
@mcp.tool()
def get_sales_order_metadata() -> dict:
    if not os.path.exists(METADATA_FILE):
        return {"error": "Metadata file not found. Call load_sap_metadata first."}

    try:
        tree = ET.parse(METADATA_FILE)
        root = tree.getroot()
        ns = {
            "edmx": "http://schemas.microsoft.com/ado/2007/06/edmx",
            "edm": "http://schemas.microsoft.com/ado/2008/09/edm"
        }

        schema = root.find(".//edm:Schema", ns)
        if schema is None:
            return {"error": "Schema not found"}

        entity_types = {}
        for et in schema.findall("edm:EntityType", ns):
            et_name = et.attrib.get("Name")
            props = []
            for prop in et.findall("edm:Property", ns):
                props.append({
                    "name": prop.attrib.get("Name"),
                    "type": prop.attrib.get("Type")
                })
            entity_types[et_name] = {"properties": props}

        entity_sets = []
        container = schema.find("edm:EntityContainer", ns)
        if container:
            for es in container.findall("edm:EntitySet", ns):
                es_name = es.attrib.get("Name")
                et_full = es.attrib.get("EntityType")
                et_short = et_full.split(".")[-1] if et_full else None

                entity_sets.append({
                    "name": es_name,
                    "entity_type": et_short,
                    "properties": entity_types.get(et_short, {}).get("properties", [])
                })

        return {
            "service": "API_SALES_ORDER_SRV",
            "entity_sets": entity_sets
        }

    except Exception as e:
        return {"error": str(e)}


# -------------------------------------------------------
# TOOL 3: Query Sales Orders
# -------------------------------------------------------
@mcp.tool()
def query_sales_orders(entity_set: str, filter: str = "", select: str = "", top: int = 20) -> dict:
    base_url = _get_service_base_url()
    params = {"$format": "json", "$top": str(top)}

    if filter:
        params["$filter"] = filter
    if select:
        params["$select"] = select

    url = f"{base_url}/{entity_set}"

    try:
        response = requests.get(
            url,
            auth=(SAP_USERNAME, SAP_PASSWORD),
            headers={"Accept": "application/json"},
            params=params,
            timeout=30
        )

        if response.status_code != 200:
            return {"error": response.text, "status": response.status_code}

        return response.json()

    except Exception as e:
        return {"error": str(e)}


# -------------------------------------------------------
# START SERVER
# -------------------------------------------------------
mcp.run()
