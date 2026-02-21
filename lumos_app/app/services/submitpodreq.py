import requests
import json
import os
import logging

# ==========================================================
# Configuration
# ==========================================================

FLASK_ENV = os.getenv("FLASK_ENV", "DEV")
NGINX_PORT = os.getenv("NGINX_PORT", "8080")

podman_hosts = [
    "http://10.54.229.197:61191",
    "http://10.10.130.57:61191"
]

proxies = {
    "http": "",
    "https": ""
}

os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""

logging.basicConfig(level=logging.INFO)


# ==========================================================
# Health Check
# ==========================================================
def check_podman_health(host):
    try:
        response = requests.get(
            f"{host}/_ping",
            timeout=5,
            verify=False,
            proxies=proxies
        )
        return response.status_code == 200
    except Exception:
        return False


# ==========================================================
# Get Container Count
# ==========================================================
def get_container_count(host):
    try:
        response = requests.get(
            f"{host}/v4.8.0/libpod/containers/json",
            timeout=10,
            verify=False,
            proxies=proxies
        )

        if response.status_code == 200:
            return len(response.json())
        else:
            logging.error(f"Failed to fetch containers from {host}")
            return float("inf")

    except Exception as e:
        logging.error(f"Error fetching container count: {e}")
        return float("inf")


# ==========================================================
# Load Balancer
# ==========================================================
def get_least_loaded_host(env):

    least_loaded_host = None
    least_container_count = float("inf")

    # Example env grouping logic
    if env in ["Mars", "Bacchus", "Pluto", "Athena"]:
        selected_hosts = podman_hosts[:1]
    elif env in ["Nexon", "CST2", "Ford", "DEVS"]:
        selected_hosts = podman_hosts[1:]
    else:
        selected_hosts = podman_hosts

    for host in selected_hosts:
        if check_podman_health(host):
            container_count = get_container_count(host)

            logging.info(f"{host} -> {container_count} containers")

            if container_count < least_container_count:
                least_container_count = container_count
                least_loaded_host = host

    if least_loaded_host:
        logging.info(
            f"Least loaded host: {least_loaded_host} "
            f"({least_container_count} containers)"
        )
    else:
        logging.error("No healthy Podman hosts found!")

    return least_loaded_host


# ==========================================================
# Create Container via REST API
# ==========================================================
def create_container(host, env, testcases, userid,
                     browser, screencapture, execid, freq):

    image = (
        "localhost/lumoslite_lean:latest"
        if browser.lower() == "chrome"
        else "localhost/lumoslite_edge:latest"
    )

    lumos_command = (
        f"python /appfs/{FLASK_ENV}/Lumos/Lumos_main.py "
        f"{env} {testcases} {userid} {execid} "
        f"{browser} {screencapture} {freq}"
    )

    container_config = {
        "Image": image,
        "Cmd": ["sh", "-c", lumos_command],
        "HostConfig": {
            "Binds": ["/appfs:/appfs"],
            "NetworkMode": "host"
        },
        "Env": [
            f"FLASK_ENV={FLASK_ENV}",
            f"NGINX_PORT={NGINX_PORT}"
        ],
        "name": execid
    }

    headers = {"Content-Type": "application/json"}

    try:
        # Create container
        response = requests.post(
            f"{host}/v4.8.0/libpod/containers/create",
            headers=headers,
            data=json.dumps(container_config),
            verify=False,
            proxies=proxies,
            timeout=15
        )

        if response.status_code != 201:
            logging.error(f"Container creation failed: {response.text}")
            return None

        container_id = response.json().get("Id")

        # Start container
        start_resp = requests.post(
            f"{host}/v4.8.0/libpod/containers/{container_id}/start",
            verify=False,
            proxies=proxies,
            timeout=10
        )

        if start_resp.status_code != 204:
            logging.error("Failed to start container")
            return None

        logging.info(f"Container started: {container_id}")
        return container_id

    except Exception as e:
        logging.error(f"Error creating container: {e}")
        return None


# ==========================================================
# Main Entry Function
# ==========================================================
def runpod(env, testcases, userid,
           browser, screencapture, execid, freq):

    logging.info("Starting runpod...")

    least_loaded_host = get_least_loaded_host(env)

    if not least_loaded_host:
        return "Nohostfound"

    container_id = create_container(
        least_loaded_host,
        env,
        testcases,
        userid,
        browser,
        screencapture,
        execid,
        freq
    )

    return container_id if container_id else "Nohostfound"


# ==========================================================
# Manual Test
# ==========================================================
if __name__ == "__main__":
    runpod(
        env="Mars",
        testcases="IVVT_MARS_SOGEA_PORTAL_PROVIDE",
        userid="Mahesh",
        browser="Chrome",
        screencapture="N",
        execid="28250414122220",
        freq="Once"
    )
