from mcp.server.fastmcp import tool
from shared.credentials import save_credentials, load_credentials

@tool()
def set_sap_credentials(username: str, password: str, metadata_url: str):
    save_credentials(username, password, metadata_url)
    return "SAP credentials saved successfully!"
