import requests

def call_sap(url, username, password, params=None, headers=None):
    resp = requests.get(
        url,
        auth=(username, password),
        params=params,
        headers=headers or {"Accept": "application/json"},
        timeout=30
    )
    return resp
