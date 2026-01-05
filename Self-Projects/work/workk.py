import os
import re
import pandas as pd
import pyodbc
from datetime import datetime

FOLDER_PATH = r"D:\CaseReports"
ACCESS_DB_PATH = r"D:\case_reports.accdb"
TABLE_NAME = "Case_Reports_Snapshots"

# Regex to extract date from filename like: Case_Reports 11-12-2025.xlsx
DATE_PATTERN = r"(\d{2}-\d{2}-\d{4})"

conn_str = (
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    rf"DBQ={ACCESS_DB_PATH};"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()


def extract_file_date(filename: str) -> datetime:
    match = re.search(DATE_PATTERN, filename)
    if not match:
        raise ValueError(f"Date not found in filename: {filename}")
    return datetime.strptime(match.group(1), "%d-%m-%Y").date()
    
    for file in os.listdir(FOLDER_PATH):
    if not file.lower().endswith(".xlsx"):
        continue

    file_path = os.path.join(FOLDER_PATH, file)

    # 1. Extract file date
    file_date = extract_file_date(file)

    # 2. Read Excel
    df = pd.read_excel(file_path)

    # 3. Add File_Date column
    df["File_Date"] = file_date

    # 4. Normalize column names (VERY IMPORTANT for Access)
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(" ", "_")
        .str.replace(r"[^\w]", "", regex=True)
    )

    # 5. Insert row by row
    cols = list(df.columns)
    placeholders = ",".join(["?"] * len(cols))
    col_names = ",".join(cols)

    insert_sql = f"""
        INSERT INTO {TABLE_NAME} ({col_names})
        VALUES ({placeholders})
    """

    for row in df.itertuples(index=False, name=None):
        cursor.execute(insert_sql, row)

    conn.commit()
    print(f"Loaded {file} ({len(df)} rows)")
    
cursor.close()
conn.close()