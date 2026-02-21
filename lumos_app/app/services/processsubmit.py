import datetime
import logging
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..db_utils import execute_query
from submitpodreq import runpod


# ==========================================================
# Configure Logging
# ==========================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)


# ==========================================================
# Update Execution Status
# ==========================================================
def update_execution_status(execid, status):
    try:
        updated = execute_query("""
            UPDATE lumos.executions
            SET exec_status = %s
            WHERE rowid = %s
        """, (status, execid), commit=True)

        return updated

    except Exception as e:
        logging.error(f"Error updating execution status: {e}")
        return 0


# ==========================================================
# Fetch Submitted Records
# ==========================================================
def get_submitted_records():
    try:
        current_time = datetime.datetime.utcnow()

        rows = execute_query("""
            SELECT rowid,
                   lumos_user,
                   exec_id,
                   env_name,
                   exec_test_list,
                   browser,
                   exec_status,
                   total_count,
                   pass_count,
                   fail_count,
                   frequency,
                   scheduled_dt,
                   screen_capture
            FROM lumos.executions
            WHERE exec_status = 'Submitted'
              AND scheduled_dt <= %s
              AND inactiveflag = 'N'
        """, (current_time,), fetch="all") or []

        columns = [
            "rowid",
            "lumos_user",
            "exec_id",
            "env_name",
            "exec_test_list",
            "browser",
            "exec_status",
            "total_count",
            "pass_count",
            "fail_count",
            "frequency",
            "scheduled_dt",
            "screen_capture"
        ]

        return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        logging.error(f"Error fetching submitted records: {e}")
        return []


# ==========================================================
# Process Single Execution Row
# ==========================================================
def process_row(row):
    try:
        logging.info(f"Processing execution: {row.get('rowid')}")

        env = row.get("env_name")
        user = row.get("lumos_user")
        execid = row.get("rowid")
        browser = row.get("browser")
        screencapture = row.get("screen_capture")
        freq = row.get("frequency")

        exec_test_list = row.get("exec_test_list", "")

        # Normalize test list
        test_list = exec_test_list.replace(".tp", ".testpack").replace(".tc", "")
        test_list = ",".join([s.strip() for s in test_list.split(",") if s.strip()])

        # Run pod
        result = runpod(env, test_list, user, browser, screencapture, execid, freq)

        if result == "Nohostfound":
            logging.error(f"Error processing execution {execid}: Host not found")
            update_execution_status(execid, "Failed")
        else:
            update_execution_status(execid, "Started")
            logging.info(f"Execution {execid} started successfully")

    except Exception as e:
        logging.error(f"Exception while processing execution {row.get('rowid')}: {e}")
        update_execution_status(row.get("rowid"), "Failed")


# ==========================================================
# Process All Submitted Records in Parallel
# ==========================================================
def process_submitted_records():
    rows = get_submitted_records()

    if not rows:
        logging.info("No submitted executions found.")
        return

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_row, row) for row in rows]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Exception in thread execution: {e}")


# ==========================================================
# Main Entry Point
# ==========================================================
if __name__ == "__main__":
    process_submitted_records()
