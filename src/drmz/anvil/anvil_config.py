# src/drmz/anvil/anvil_config.py

import os
import requests

# ✅ Correct base URL for Ada Anvil
DEFAULT_ANVIL_URL = "https://dev.ada-anvil.io"
ANVIL_API_URL = os.getenv("ANVIL_API_URL", DEFAULT_ANVIL_URL)

# Optional headers (add auth or content-type if needed)
HEADERS = {
    "Content-Type": "application/json"
}

def call_anvil_api(endpoint: str, method: str = "GET", payload: dict = None):
    """
    Generic caller for Ada Anvil API endpoints.

    Args:
        endpoint (str): e.g., "/simulate/mint"
        method (str): "GET" or "POST"
        payload (dict): For POST requests

    Returns:
        dict | None: Parsed JSON or None on error
    """
    url = f"{ANVIL_API_URL}/{endpoint.lstrip('/')}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=HEADERS)
        else:
            response = requests.post(url, json=payload, headers=HEADERS)

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"❌ Anvil API error at {url}: {e}")
        return None
