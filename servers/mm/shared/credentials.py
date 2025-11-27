import os
from dotenv import load_dotenv

def load_credentials(env_path=".env"):
    load_dotenv(env_path)
    return (
        os.getenv("SAP_USERNAME"),
        os.getenv("SAP_PASSWORD"),
        os.getenv("SAP_METADATA_URL"),
    )

def save_credentials(username, password, metadata_url, env_path=".env"):
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f"SAP_USERNAME={username}\n")
        f.write(f"SAP_PASSWORD={password}\n")
        f.write(f"SAP_METADATA_URL={metadata_url}\n")
