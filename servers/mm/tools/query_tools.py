
from shared.credentials import load_credentials
from shared.sap_http import call_sap


def query_billing_documents(entity_set: str, filter: str = "", select: str = "", top: int = 20):
    username, password, metadata_url = load_credentials()

    if not (username and password and metadata_url):
        return {"error": "missing_credentials"}

    base = metadata_url.replace("/$metadata", "")
    url = f"{base}/{entity_set}"

    params = {"$format": "json", "$top": str(top)}
    if filter: params["$filter"] = filter
    if select: params["$select"] = select

    resp = call_sap(url, username, password, params=params)

    if resp.status_code != 200:
        return {"error": resp.text, "status": resp.status_code}

    return resp.json()
