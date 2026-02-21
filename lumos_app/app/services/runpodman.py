import os
import subprocess
import logging


# ==========================================================
# Configuration
# ==========================================================
FLASK_ENV = os.getenv("FLASK_ENV", "DEV")
IMAGE_NAME = "localhost/lumosedge:latest"


# ==========================================================
# Run Podman Container
# ==========================================================
def runpod(env, test_list, user, browser, screencapture, execid, frequency):
    """
    Run Lumos container using Podman.
    Returns container ID if success, else error string.
    """

    try:
        # Construct command to execute inside container
        lumos_command = (
            f"python /appfs/{FLASK_ENV}/Lumos_edge/Lumos.py "
            f"{env} Y {test_list}"
        )

        print(f"Executing Lumos Command: {lumos_command}")

        # Full podman command
        podman_cmd = [
            "podman",
            "run",
            "-d",                        # detached mode
            "--rm",                       # remove container after exit
            "-v", "/appfs:/appfs",        # bind mount
            IMAGE_NAME,
            "sh",
            "-c",
            lumos_command
        ]

        result = subprocess.run(
            podman_cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logging.error(f"Podman Error: {result.stderr}")
            return "Nohostfound"

        container_id = result.stdout.strip()

        logging.info(f"Container started: {container_id}")

        return container_id

    except Exception as e:
        logging.error(f"Exception in runpod: {e}")
        return "Nohostfound"


# ==========================================================
# Manual Test Runner
# ==========================================================
if __name__ == "__main__":
    test_env = "DEV"
    test_case = "10000_Sample_Login"

    container_id = runpod(
        env=test_env,
        test_list=test_case,
        user="admin",
        browser="chrome",
        screencapture="Y",
        execid="123456",
        frequency="Once"
    )

    print("Container ID:", container_id)
