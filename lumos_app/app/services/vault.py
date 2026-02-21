import os
import requests
import logging
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable SSL warning (only if required in non-prod)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logging.basicConfig(level=logging.INFO)


def get_access_token():
    """
    Fetch Lumos Web Bit Token from Vault securely.
    """

    key = "Lumosweb_BitToken"

    vault_url = os.getenv(
        "VAULT_URL",
        "https://vault-new.aws.mobius.nat.bt.com/v1/APP_OR_SABOR/data/kv/nonprod"
    )

    vault_token = os.getenv("VAULT_TOKEN")

    if not vault_token:
        logging.error("Vault token not found in environment variables.")
        return None

    headers = {
        "Accept": "application/json",
        "X-Vault-Token": vault_token
    }

    proxies = {
        "http": os.getenv("HTTP_PROXY", ""),
        "https": os.getenv("HTTPS_PROXY", "")
    }

    try:
        response = requests.get(
            vault_url,
            headers=headers,
            verify=False,   # Set True in production if cert valid
            proxies=proxies,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        return data.get("data", {}).get("data", {}).get(key)

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Vault HTTP Error: {http_err}")
        if http_err.response:
            logging.error(f"Response content: {http_err.response.text}")
        return None

    except requests.exceptions.RequestException as req_err:
        logging.error(f"Vault Request Error: {req_err}")
        return None

    except Exception as e:
        logging.error(f"Unexpected error while fetching token: {e}")
        return None
