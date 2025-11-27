
import os
import requests
from shared.credentials import load_credentials
from shared.metadata_parser import parse_metadata

METADATA_FILE = "metadata/API_BILLING_DOCUMENT_SRV.xml"


def load_billing_metadata():
    username, password, url = load_credentials()

    if not (username and password and url):
        return "missing_credentials"

    resp = requests.get(url, auth=(username, password), headers={"Accept": "application/xml"})
    if resp.status_code != 200:
        return f"Failed: {resp.status_code}"

    os.makedirs("metadata", exist_ok=True)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        f.write(resp.text)

    return "Metadata loaded!"


def get_billing_document_metadata():
    if not os.path.exists(METADATA_FILE):
        return {"error": "metadata_missing"}

    return {"entity_sets": parse_metadata(METADATA_FILE)}
