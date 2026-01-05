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
        raise ValueError("Filename does not match pattern")
    return datetime.strptime(match.group(1), "%d-%m-%Y").date()


def infer_schema_from_excel(folder_path: str) -> list[str]:
    for file in os.listdir(folder_path):
        if file.endswith(".xlsx"):
            df = pd.read_excel(os.path.join(folder_path, file), nrows=1)
            df = df.rename(columns={"Title": "AccountNumber"})
            return list(df.columns)
    raise RuntimeError("No Excel files found")


def ensure_table_exists(column_names: list[str]):
    conn = get_access_connection()
    cursor = conn.cursor()

    columns_sql = []
    for col in column_names:
        if col == "FileDate":
            columns_sql.append(f"[{col}] DATE")
        elif col == "LoadTimestamp":
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
    except pyodbc.Error:
        # Table already exists → safe to ignore
        pass

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
        print("No new data to insert")
        return

    conn = get_access_connection()
    cursor = conn.cursor()

    columns = list(df.columns)
    column_str = ",".join(f"[{c}]" for c in columns)
    placeholders = ",".join("?" for _ in columns)

    insert_sql = f"""
        INSERT INTO {TABLE_NAME} ({column_str})
        VALUES ({placeholders})
    """

    for row in df.itertuples(index=False, name=None):
        cursor.execute(insert_sql, row)

    conn.commit()
    conn.close()

    print(f"Inserted {len(df)} rows")


def main():
    base_columns = infer_schema_from_excel(FOLDER_PATH)

    for col in ("FileDate", "LoadTimestamp"):
        if col not in base_columns:
            base_columns.append(col)

    ensure_table_exists(base_columns)

    last_loaded_date = get_max_file_date_from_access()
    print(f"Last loaded FileDate: {last_loaded_date}")

    df = load_incremental_files(FOLDER_PATH, last_loaded_date)
    insert_into_access(df)


if __name__ == "__main__":
    main()