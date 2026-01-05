import os
import re
from datetime import datetime, date
import pandas as pd
import pyodbc

# ---------------- CONFIG ----------------
FOLDER_PATH = r"D:\RR_SOW_FILES"
ACCESS_DB_PATH = r"D:\RR_DB\rr_data.accdb"
TABLE_NAME = "RR_SOW_Snapshots"

FILE_PATTERN = r"RR_SOW_(\d{2}-\d{2}-\d{4})\.xlsx"
# ----------------------------------------

def get_access_connection():
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={ACCESS_DB_PATH};"
    )
    return pyodbc.connect(conn_str)

def extract_date_from_filename(filename: str) -> date:
    match = re.search(FILE_PATTERN, filename)
    if not match:
        raise ValueError(f"Invalid filename: {filename}")
    return datetime.strptime(match.group(1), "%d-%m-%Y").date()

def get_max_file_date_from_access() -> date | None:
    conn = get_access_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT MAX(FileDate) FROM {TABLE_NAME}")
    result = cursor.fetchone()[0]

    conn.close()
    return result  # None if table is empty

def load_incremental_files(folder_path: str, last_loaded_date: date | None) -> pd.DataFrame:
    dfs = []

    for file in os.listdir(folder_path):
        if not file.endswith(".xlsx"):
            continue

        try:
            file_date = extract_date_from_filename(file)
        except ValueError:
            continue  # ignore unrelated files

        if last_loaded_date and file_date <= last_loaded_date:
            continue  # incremental filter

        file_path = os.path.join(folder_path, file)
        df = pd.read_excel(file_path)

        # Rename and standardize
        df = df.rename(columns={"Title": "AccountNumber"})
        df["AccountNumber"] = df["AccountNumber"].astype(str).str.strip()

        df["FileDate"] = file_date
        df["LoadTimestamp"] = datetime.now()

        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)

def insert_into_access(df: pd.DataFrame):
    if df.empty:
        print("No new files to load.")
        return

    conn = get_access_connection()
    cursor = conn.cursor()

    columns = list(df.columns)
    placeholders = ",".join(["?"] * len(columns))
    column_str = ",".join(columns)

    insert_sql = f"""
        INSERT INTO {TABLE_NAME} ({column_str})
        VALUES ({placeholders})
    """

    cursor.fast_executemany = True
    cursor.executemany(insert_sql, df.values.tolist())

    conn.commit()
    conn.close()

    print(f"Inserted {len(df)} rows")

def main():
    last_loaded_date = get_max_file_date_from_access()
    print(f"Last loaded FileDate in Access: {last_loaded_date}")

    df = load_incremental_files(FOLDER_PATH, last_loaded_date)
    insert_into_access(df)

if __name__ == "__main__":
    main()