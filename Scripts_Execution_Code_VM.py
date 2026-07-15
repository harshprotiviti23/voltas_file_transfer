from dotenv import load_dotenv

# ---------- Load .env ----------

load_dotenv()


HOST     = os.getenv("DB_HOST")
USER     = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
DATABASE = os.getenv("DB_DATABASE")

if not all([HOST, USER, PASSWORD, DATABASE]):
    raise ValueError("One or more DB environment variables are missing. Check your .env file.")






=====================================================







SOURCE_FOLDER=r'\\vlfidacrmfilepreprod.file.core.windows.net\vlfidacrmfilesharepreprod\data'
JPG_FOLDER = r"\\vlfidacrmfilepreprod.file.core.windows.net\vlfidacrmfilesharepreprod\jpg"
FINAL_FOLDER = r"\\vlfidacrmfilepreprod.file.core.windows.net\vlfidacrmfilesharepreprod\inv_jpg"
POPPLER_PATH=r'\\vlfidacrmfilepreprod.file.core.windows.net\vlfidacrmfilesharepreprod\Poppler\Release-24.02.0-0\poppler-24.02.0\Library\bin'










=======================================================================












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

# Load environment variables
load_dotenv()

# ==============================
# 🌐 NETWORK DRIVE MAPPING
# ==============================
SMB_SHARE_ROOT = os.environ.get('SMB_SHARE_ROOT')
SMB_USERNAME = os.environ.get('SMB_USERNAME')
SMB_PASSWORD = os.environ.get('SMB_PASSWORD')

def connect_smb():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Removing existing SMB connection if any...")
    subprocess.run(
        ["net", "use", SMB_SHARE_ROOT, "/delete", "/y"],
        capture_output=True, text=True, shell=False
    )

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connecting to SMB share using username/password...")
    cmd = [
        "net", "use", SMB_SHARE_ROOT, SMB_PASSWORD,
        f"/user:{SMB_USERNAME}", "/persistent:no"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, shell=False)

    if result.returncode != 0:
        print(f"net use stderr:\n{result.stderr}")
        raise Exception("Failed to connect to SMB share using net use")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] SMB share connected successfully.")

# Map drive before doing anything else
connect_smb()



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
    

table_name = "t_claim_process"
query = f"UPDATE {table_name} set status='In-Progress' where status is NULL"
cursor.execute(query)

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
                ["python", "-u", file],
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
    
    {"check_id": "5000", "type": "python", "file": "Data_Extraction.py", "mode": "sequential"},
    {"check_id": "5001", "type": "sql", "file": "base_data_creation_code.sql", "mode": "sequential"},
    {"check_id": "5002", "type": "python", "file": "Claim_Filtering_JPG_Conversion.py", "mode": "sequential"},
    {"check_id": "5003", "type": "python",    "file": "code_unstructure_structure.py", "mode": "sequential"},
    {"check_id": "5004", "type": "python", "file": "base_data_v1_creation_code.py", "mode": "sequential"},
    {"check_id": "5005", "type": "python",    "file": "File_Names_Extraction.py", "mode": "sequential"},

    # # 🔹 24 Parallel Scripts
    # # # /*************************Rule Based Analytics Scripts**************/
    {"check_id": "1001", "type": "sql", "file": "Duplicate_Expense_Detection.sql", "mode": "parallel"},
    {"check_id": "1002", "type": "sql",    "file": "Invoice_Sequence_Exception.sql", "mode": "parallel"},
    {"check_id": "1003", "type": "sql", "file": "Keyword_Analysis.sql", "mode": "parallel"},
    {"check_id": "1004", "type": "sql",    "file": "Receipt_Compliance.sql", "mode": "parallel"},
    {"check_id": "1005", "type": "sql", "file": "Expense_submission_delay.sql", "mode": "parallel"},
    {"check_id": "1006", "type": "sql",    "file": "Repeated_Same_Claim_Amount.sql", "mode": "parallel"},
    # # # # # /******************************Image Analytics Scripts******************/
    {"check_id": "2001", "type": "python", "file": "Image_Duplicate.py", "mode": "parallel"},
    #{"check_id": "2002", "type": "python",    "file": "Pdf_Edit_Exception.py", "mode": "parallel"},
    {"check_id": "2003", "type": "python", "file": "Image_Edit_Exception.py", "mode": "parallel"},
    {"check_id": "2004", "type": "python",    "file": "QR_Code_Exception.py", "mode": "parallel"},
    {"check_id": "2005", "type": "python", "file": "MetaData_Exception.py", "mode": "parallel"},
    
    # # # {"check_id": "2006", "type": "python",    "file": "AI_Image_Identifier.py", "mode": "parallel"},
    # # /******************************External Intelligence Scripts******************/
    {"check_id": "3001", "type": "python", "file": "Travel_Distance.py", "mode": "parallel"},
    # # # {"check_id": "3003", "type": "python",    "file": "Vendor_Validation.py", "mode": "parallel"},
    # # # # /******************************ML Outlier Scripts******************/    
    {"check_id": "4007", "type": "python", "file": "Multiple_Bills_Same_Day.py", "mode": "parallel"},
    {"check_id": "4012", "type": "python",    "file": "Multiple_Bills_Same_Vendor_Same_Day.py", "mode": "parallel"},
    {"check_id": "4013", "type": "python", "file": "Employee_Vendor_Concentration.py", "mode": "parallel"},
    {"check_id": "4015", "type": "python",    "file": "High_Handwritten_Bills.py", "mode": "parallel"},
    {"check_id": "4018", "type": "python", "file": "Peer_Spend_Comparison.py", "mode": "parallel"},
    {"check_id": "4019", "type": "python",    "file": "Spend_Overview.py", "mode": "parallel"},
    {"check_id": "40201", "type": "python", "file": "Employee_Same_Amount_Repeated_Ratio.py", "mode": "parallel"},
    {"check_id": "4021", "type": "python",    "file": "Spend_By_Expense_Category.py", "mode": "parallel"},
    {"check_id": "4022", "type": "python", "file": "Vendor_Usage_Across_Employee.py", "mode": "parallel"},
    {"check_id": "4023", "type": "python",    "file": "High_Value_Exception_Expense_Type.py", "mode": "parallel"},
    {"check_id": "6002", "type": "python", "file": "MetaData_Exception_Insertion.py", "mode": "parallel"}
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
   
        if result.returncode == 0:
            print("Final script executed successfully")

            conn = pymysql.connect(host=HOST, user=USER, password=PASSWORD, database=DATABASE,port=3306, ssl =ssl_config )
            cursor = conn.cursor()
            sp_list = [
                    "sp_refresh_view_rbv_exception_facts_mv",
                    "sp_refresh_view_rbv_analytics_details_mv",
                    "sp_refresh_view_image_analytics_exception_facts_mv",
                    "sp_refresh_view_image_analytics_details_mv",
                    "sp_refresh_view_external_intelligence_exception_facts_mv",
                    "sp_refresh_view_ei_analytics_details_mv",
                    "sp_refresh_view_ml_rules_exception_facts_mv",
                    "sp_refresh_view_ml_analytics_details_mv",
                    "sp_update_claim_process_completed",
                    "sp_refresh_mv_view_dashboard_claim_overall_analysis",
                    "sp_refresh_view_api_response_mv",
                    "sp_refresh_mv_view_dashboard_claim_drilldown",
                    "sp_refresh_mv_view_dashboard_kpi_summary"
                ]

            for sp in sp_list:
                sp_start = datetime.now()

                try:
                    print(f"Executing {sp}")

                    cursor.execute(f"CALL {sp}()")

                    while cursor.nextset():
                        pass

                    conn.commit()

                    sp_end = datetime.now()

                    log_to_db(
                            check_id="9001",
                            script_name=sp,
                            script_type="STORED_PROCEDURE",
                            status="SUCCESS",
                            error_message=None,
                            start_time=sp_start,
                            end_time=sp_end
                        )

                except Exception as e:
                    sp_end = datetime.now()

                    log_to_db(
                            check_id="SP",
                            script_name=sp,
                            script_type="STORED_PROCEDURE",
                            status="FAILED",
                            error_message=str(e),
                            start_time=sp_start,
                            end_time=sp_end
                        )

                    print(f"{sp} failed: {e}")

        else:
            print(" Final script failed:", result.stderr)
    
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
         
    
    
