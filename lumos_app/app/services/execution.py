from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import os

from ..db_utils import execute_query


# ==========================================================
# Fetch Scheduled Executions
# ==========================================================
def fetch_scheduled_executions():
    """
    Fetch all executions that are scheduled and still in 'Submitted' status.
    """

    try:
        current_time = datetime.now()

        rows = execute_query("""
            SELECT lumos_user,
                   exec_id,
                   exec_date,
                   env_name,
                   exec_status,
                   total_count,
                   pass_count,
                   fail_count,
                   exec_time,
                   browser,
                   parallel_exec,
                   delay,
                   screen_capture,
                   inactiveflag,
                   orgid,
                   frequency,
                   scheduled_dt,
                   exec_test_list
            FROM lumos.executions
            WHERE scheduled_dt <= %s
              AND exec_status = 'Submitted'
              AND inactiveflag = 'N'
        """, (current_time,), fetch="all") or []

        executions = []

        for row in rows:
            executions.append({
                "lumos_user": row[0],
                "exec_id": row[1],
                "exec_date": row[2],
                "env_name": row[3],
                "exec_status": row[4],
                "total_count": row[5],
                "pass_count": row[6],
                "fail_count": row[7],
                "exec_time": row[8],
                "browser": row[9],
                "parallel_exec": row[10],
                "delay": row[11],
                "screen_capture": row[12],
                "inactiveflag": row[13],
                "orgid": row[14],
                "frequency": row[15],
                "scheduled_dt": row[16],
                "exec_test_list": row[17]
            })

        return executions

    except Exception as e:
        print(f"Failed to fetch scheduled executions: {e}")
        return []


# ==========================================================
# Process Executions in Parallel
# ==========================================================
def process_executions_in_parallel(executions):
    """
    Process multiple executions using threads.
    """

    def process_execution(execution):

        try:
            exec_test_list = execution.get("exec_test_list")

            if not exec_test_list:
                return

            tests = exec_test_list.split(',')

            test_dict = {}

            for i, test in enumerate(tests):
                test = test.strip()

                if test:
                    test_dict[f"test_{i+1}"] = test

            env = execution.get("env_name")

            call_lumos(test_dict, env, trigger_flag="Y")

        except Exception as e:
            print(f"Execution processing failed: {e}")

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(process_execution, exe) for exe in executions]

        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"Thread execution failed: {e}")


# ==========================================================
# Call Lumos Runner
# ==========================================================
def call_lumos(test_dict, env, trigger_flag="Y"):
    """
    Trigger Lumos test runner using system command.
    """

    try:
        test_names = ",".join(test_dict.values())

        command = f"python Lumos.py {env} {trigger_flag} {test_names}"

        print(f"Running command: {command}")

        os.system(command)

    except Exception as e:
        print(f"Error executing Lumos command: {e}")


# ==========================================================
# Main Scheduler Function
# ==========================================================
def run_scheduler():
    """
    Fetch scheduled executions and process them.
    """

    executions = fetch_scheduled_executions()

    if not executions:
        print("No scheduled executions found.")
        return

    process_executions_in_parallel(executions)
