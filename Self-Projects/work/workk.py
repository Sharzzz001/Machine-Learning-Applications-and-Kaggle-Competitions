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

def infer_schema_from_excel(folder_path: str) -> list[str]:
    for file in os.listdir(folder_path):
        if file.endswith(".xlsx"):
            df = pd.read_excel(os.path.join(folder_path, file), nrows=1)
            df = df.rename(columns={"Title": "AccountNumber"})
            return list(df.columns)
    raise RuntimeError("No Excel files found to infer schema")

def ensure_table_exists(column_names: list[str]):
    conn = get_access_connection()
    cursor = conn.cursor()

    columns_sql = []
    for col in column_names:
        if col in ("FileDate",):
            columns_sql.append(f"[{col}] DATE")
        elif col in ("LoadTimestamp",):
            columns_sql.append(f"[{col}] DATETIME")
        else:
            columns_sql.append(f"[{col}] TEXT(255)")

    create_sql = f"""
    CREATE TABLE {TABLE_NAME} (
        {', '.join(columns_sql)}
    )
    """

    try:
        cursor.execute(create_sql)
        conn.commit()
        print(f"Table {TABLE_NAME} created")
    except pyodbc.Error as e:
        if "already exists" not in str(e).lower():
            raise

    conn.close()

def get_max_file_date_from_access() -> date | None:
    conn = get_access_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT MAX(FileDate) FROM {TABLE_NAME}")
        result = cursor.fetchone()[0]
    except pyodbc.Error:
        result = None

    conn.close()
    return result

def load_incremental_files(folder_path: str, last_loaded_date: date | None) -> pd.DataFrame:
    dfs = []

    for file in os.listdir(folder_path):
        if not file.endswith(".xlsx"):
            continue

        try:
            file_date = extract_date_from_filename(file)
        except ValueError:
            continue

        if last_loaded_date and file_date <= last_loaded_date:
            continue

        df = pd.read_excel(os.path.join(folder_path, file))
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
    column_str = ",".join(f"[{c}]" for c in columns)

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
    # Step 1: Infer schema from Excel
    base_columns = infer_schema_from_excel(FOLDER_PATH)

    # Ensure metadata columns exist
    for col in ("FileDate", "LoadTimestamp"):
        if col not in base_columns:
            base_columns.append(col)

    # Step 2: Create table if missing
    ensure_table_exists(base_columns)

    # Step 3: Incremental load
    last_loaded_date = get_max_file_date_from_access()
    print(f"Last loaded FileDate: {last_loaded_date}")

    df = load_incremental_files(FOLDER_PATH, last_loaded_date)
    insert_into_access(df)

if __name__ == "__main__":
    main()