import os
import re
import requests
import logging

from ..db_utils import execute_query


# ==========================================================
# Configuration
# ==========================================================

FLASK_ENV = os.getenv("FLASK_ENV", "DEV")

servers = [
    {"host": "http://18.54.229.197:61191"},
    {"host": "http://10.10.130.57:61191"},
    {"host": "http://10.10.130.58:61191"},
    {"host": "http://10.10.129.148:61191"},
    {"host": "http://10.10.129.149:61191"},
    {"host": "http://10.18.129.150:61191"},
]

# Optional proxy config (leave empty if not required)
proxies = {
    "http": "",
    "https": ""
}

os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""

logging.basicConfig(level=logging.INFO)


# ==========================================================
# Stop Containers by Execution ID
# ==========================================================
def stop_containers_by_execution_id(execution_id, username):
    """
    Stops containers on all configured servers whose
    names start with the given execution ID.
    """

    name_pattern = rf"^{re.escape(str(execution_id))}"

    def stop_matching_containers(server):
        base_url = server["host"]
        containers_url = f"{base_url}/v4.8.0/libpod/containers/json"

        try:
            response = requests.get(containers_url, proxies=proxies, timeout=10)
            response.raise_for_status()

            containers = response.json()

            for container in containers:
                names = container.get("Names", [])
                if not names:
                    continue

                name = names[0].lstrip("/")

                if re.match(name_pattern, name):
                    container_id = container.get("Id")

                    stop_url = f"{base_url}/v4.8.0/libpod/containers/{container_id}/stop"

                    logging.info(f"Stopping container {name} on {base_url}")

                    stop_resp = requests.post(stop_url, proxies=proxies, timeout=15)
                    stop_resp.raise_for_status()

                    logging.info(f"Container {name} stopped successfully.")

        except Exception as e:
            logging.error(f"Error on server {base_url}: {e}")

    # Stop containers on all servers
    for server in servers:
        stop_matching_containers(server)

    # Update execution status in DB
    try:
        execute_query("""
            UPDATE lumos.executions
            SET exec_status = %s,
                lastupdby = %s
            WHERE rowid = %s
        """, ("Stopped", username, execution_id), commit=True)

        logging.info(f"Execution {execution_id} marked as Stopped.")

    except Exception as e:
        logging.error(f"Failed to update execution status: {e}")
