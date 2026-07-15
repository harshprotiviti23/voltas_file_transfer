import sys


log_path= r"F:/PythonBackgroundProcess/python_processing_job.txt"
sys.stdout = open(log_path,"a",encoding="utf-8",errors="replace")
sys.stderr = sys.stdout


import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import pymysql
import os
import pandas as pd
from types import SimpleNamespace
import traceback
from dotenv import load_dotenv
import argparse

# Load environment variables
load_dotenv()


parser = argparse.ArgumentParser()
parser.add_argument("--ids", required=True, help="Comma-separated list of IDs")

args = parser.parse_args()

ids = [int(x) for x in args.ids.split(",")]


BASE_DIR =  os.environ.get('BASE_DIR')
os.chdir(BASE_DIR)
process_start_time = datetime.now()

# ==============================
# 🔗 DB CONNECTION
# ==============================

HOST= os.environ.get('DB_HOST')
USER= os.environ.get('DB_USER')
PASSWORD= os.environ.get('DB_PASSWORD')
DATABASE= os.environ.get('DB_DATABASE')
MYSQL_EXE_PATH= os.environ.get('MYSQL_EXE_PATH')

ssl_config = {
        'ssl_verify_identity': True
    }

conn = pymysql.connect(host=HOST, user=USER, password=PASSWORD, database=DATABASE,port=3306, ssl =ssl_config )
cursor = conn.cursor()


# claim_ids = pd.DataFrame({"id": ids})    

# table_name = "t_claim_process"
# query = f"UPDATE {table_name} set status='In-Progress' where status is NULL"
# cursor.execute(query)

claim_ids = pd.DataFrame({"id": ids})

table_name = "t_claim_process"

# Create placeholders for parameterized query
placeholders = ",".join(["%s"] * len(claim_ids))

query = f"""
UPDATE {table_name}
SET status = 'In-Progress'
WHERE status IS NULL
  AND header_crm_id IN ({placeholders})
"""

cursor.execute(query, tuple(claim_ids["id"]))
conn.commit()

# /*********************Script for Total Claim Processed*********/
table_name = "t_claim_process"
query = f"SELECT * FROM {table_name} where status = 'In-Progress'"

cursor.execute(query)
rows = cursor.fetchall()
 
columns = [desc[0] for desc in cursor.description]
Claim_Table = pd.DataFrame(rows, columns=columns)


conn.commit()

# /*************************Variables to run sql scripts ************/
mysql_path = os.environ.get('MYSQL_EXE_PATH')
env = os.environ.copy()
env["MYSQL_PWD"] = PASSWORD
cmd = [
    mysql_path,
    "-h", HOST,
    "-u", USER ,
    "-P", "3306",
    DATABASE
]

# ==============================
# 🗄️ LOG FUNCTION
# ==============================
def log_to_db(check_id, script_name, script_type, status, error_message, start_time, end_time,no_of_claims=0):
    conn = pymysql.connect(host=HOST, user=USER, password=PASSWORD, database=DATABASE,port=3306, ssl =ssl_config )
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO t_script_execution_log 
        (check_id, script_name, script_type, status, error_message, start_time, end_time,no_of_claims)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (check_id, script_name, script_type, status, error_message, start_time, end_time,no_of_claims))
    conn.commit()

# ==============================
# ⚙️ TASK EXECUTION FUNCTION
# ==============================
def run_command_with_live_output(command, cwd=None, env=None, prefix=None):
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    output_lines = []
    for line in process.stdout:
        output_lines.append(line)
        if prefix:
            print(f"[{prefix}] {line}", end="", flush=True)
        else:
            print(line, end="", flush=True)

    return_code = process.wait()
    output = "".join(output_lines)
    return SimpleNamespace(returncode=return_code, stdout=output, stderr=output)

def run_task(task):
    check_id = task["check_id"]
    script_type = task["type"]
    file = task["file"]

    start_time = datetime.now()

    try:
        # Log STARTED
        log_to_db(check_id, file, script_type, "STARTED", None, start_time, None)

        if script_type == "python":
            # subprocess.run(["python","E:/Drishti/Codes/MetaData_Exception.py"])
            result = run_command_with_live_output(
                ["python", "-u", file,"--ids",args.ids],
                cwd=BASE_DIR,
                env=env,
                prefix=file
            )
        else:
            with open(file, "r") as f:
                result = subprocess.run(
                    cmd,
                    stdin=f,
                    capture_output=True,
                    text=True,
                    cwd=BASE_DIR,
                    env=env
                )


        end_time = datetime.now()
        if result.returncode == 0:
            log_to_db(check_id, file, script_type, "SUCCESS", None, start_time, end_time)
        else:
            log_to_db(check_id, file, script_type, "FAILED", result.stderr, start_time, end_time)

    except Exception as e:
        end_time = datetime.now()
        log_to_db(check_id, file, script_type, "FAILED", str(e), start_time, end_time)

# ==============================
# 📋 DEFINE TASKS
# ==============================

tasks = [
    # # 🔹 5 Sequential Scripts
    
    # {"check_id": "5000", "type": "python", "file": "Data_Extraction.py", "mode": "sequential"},
    {"check_id": "5001", "type": "sql", "file": "base_data_creation_code.sql", "mode": "sequential"},
    {"check_id": "5002", "type": "python", "file": "Claim_Filtering_JPG_Conversion.py", "mode": "sequential"},
    {"check_id": "5003", "type": "python",    "file": "code_unstr_str_customer_invoice.py", "mode": "sequential"},
    # # 🔹 24 Parallel Scripts
    # # # /*************************Rule Based Analytics Scripts**************/
    {"check_id": "1001", "type": "sql", "file": "table1001.py", "mode": "parallel"},
    {"check_id": "1002", "type": "sql", "file": "table1002.py", "mode": "parallel"},
    {"check_id": "1003", "type": "sql", "file": "table1003.py", "mode": "parallel"},
    {"check_id": "1004", "type": "sql", "file": "table1004.py", "mode": "parallel"},
    {"check_id": "1015", "type": "sql", "file": "table1005.py", "mode": "parallel"},
    {"check_id": "1016", "type": "sql", "file": "table1006.py", "mode": "parallel"},
    {"check_id": "1017", "type": "sql", "file": "table1007.py", "mode": "parallel"},
    {"check_id": "1018", "type": "sql", "file": "table1008.py", "mode": "parallel"},

]

# ==============================
# 🚀 MAIN EXECUTION
# ==============================
if __name__ == "__main__":

    print(" Starting Sequential Execution...")
    for task in tasks:
        if task["mode"] == "sequential":
            run_task(task)

    print(" Starting Parallel Execution...")
    parallel_tasks = [t for t in tasks if t["mode"] == "parallel"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.map(run_task, parallel_tasks)

    print("Execution Completed!")
    print(" Running Final Completion Script...")
    try:
        result = subprocess.run(
            ["python", "Final_Completion_Script.py"],
            capture_output=True,
            text=True
        )    
    except Exception as e:
          print(" Error running final script:", str(e))
    end_time = datetime.now()
    Total_Claims_Processed=len(Claim_Table)
    log_to_db(
        check_id="6001",
        script_name="FINAL_COMPLETION",
        script_type="SYSTEM",
        status="COMPLETED",
        error_message=None,
        start_time=process_start_time,
        end_time=end_time,
        no_of_claims=Total_Claims_Processed
    )     
         
    
    