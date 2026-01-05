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

TEXT_COLUMNS = [
    "AccountNumber",
    "ClientName",
    "Grouping",
    "ReviewType",
    "Risk",
    "PEP",
    "ekycID",
    "RM",
    "GH",
    "SOWStatus",
    "SOWMaker",
    "SOWChecker",
    "SOWComments",
    "RiskChange",
    "Item Type",
    "Path"
]

DATE_COLUMNS = [
    "DueDate",
    "eKYCDate",
    "AssignDate",
    "ApprovalDate",
    "FirstReviewDate"
]

DATETIME_COLUMNS = [
    "Created",
    "FileDate",
    "LoadTimestamp"
]

ALL_COLUMNS = (
    TEXT_COLUMNS
    + DATE_COLUMNS
    + DATETIME_COLUMNS
)

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
        raise ValueError("Invalid filename format")
    return datetime.strptime(match.group(1), "%d-%m-%Y").date()


# ---------- TABLE CREATION ----------

def ensure_table_exists():
    conn = get_access_connection()
    cursor = conn.cursor()

    create_sql = f"""
    CREATE TABLE {TABLE_NAME} (
        AccountNumber TEXT(50),
        ClientName TEXT(255),
        Grouping TEXT(255),
        ReviewType TEXT(255),
        Risk TEXT(50),
        PEP TEXT(50),
        ekycID TEXT(100),
        RM TEXT(100),
        GH TEXT(100),
        SOWStatus TEXT(50),
        SOWMaker TEXT(100),
        SOWChecker TEXT(100),
        SOWComments TEXT(255),
        RiskChange TEXT(50),
        [Item Type] TEXT(100),
        Path TEXT(255),

        DueDate DATE,
        eKYCDate DATE,
        AssignDate DATE,
        ApprovalDate DATE,
        FirstReviewDate DATE,

        Created DATETIME,
        FileDate DATE,
        LoadTimestamp DATETIME
    )
    """

    try:
        cursor.execute(create_sql)
        conn.commit()
        print(f"Created table {TABLE_NAME}")
    except pyodbc.Error:
        # Table already exists
        pass

    conn.close()


# ---------- INCREMENTAL CHECK ----------

def get_max_file_date():
    conn = get_access_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT MAX(FileDate) FROM {TABLE_NAME}")
        result = cursor.fetchone()[0]
    except pyodbc.Error:
        result = None

    conn.close()
    return result


# ---------- DATA CLEANING ----------

def clean_text_columns(df):
    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .replace({"nan": None, "None": None})
                .str.strip()
            )
    return df


def clean_date_columns(df):
    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
            df[col] = df[col].where(df[col].notna(), None)
    return df


def clean_datetime_columns(df):
    for col in DATETIME_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

            # Access-safe range
            df.loc[
                (df[col].dt.year < 100) | (df[col].dt.year > 9999),
                col
            ] = pd.NaT

            df[col] = df[col].where(df[col].notna(), None)
    return df


# ---------- LOAD FILES ----------

def load_incremental_files(last_loaded_date):
    dfs = []

    for file in os.listdir(FOLDER_PATH):
        if (
            not file.endswith(".xlsx")
            or file.startswith("~$")
        ):
            continue

        try:
            file_date = extract_date_from_filename(file)
        except ValueError:
            continue

        if last_loaded_date and file_date <= last_loaded_date:
            continue

        df = pd.read_excel(os.path.join(FOLDER_PATH, file))
        df = df.rename(columns={"Title": "AccountNumber"})

        df["FileDate"] = file_date
        df["LoadTimestamp"] = datetime.now()

        # Ensure all columns exist
        for col in ALL_COLUMNS:
            if col not in df.columns:
                df[col] = None

        df = df[ALL_COLUMNS]

        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)


# ---------- INSERT ----------

def insert_into_access(df):
    if df.empty:
        print("No new data to insert.")
        return

    conn = get_access_connection()
    cursor = conn.cursor()

    columns_sql = ",".join(f"[{c}]" for c in ALL_COLUMNS)
    placeholders = ",".join("?" for _ in ALL_COLUMNS)

    insert_sql = f"""
        INSERT INTO {TABLE_NAME} ({columns_sql})
        VALUES ({placeholders})
    """

    for row in df.itertuples(index=False, name=None):
        cursor.execute(insert_sql, row)

    conn.commit()
    conn.close()

    print(f"Inserted {len(df)} rows")


# ---------- MAIN ----------

def main():
    ensure_table_exists()

    last_loaded_date = get_max_file_date()
    print(f"Last loaded FileDate: {last_loaded_date}")

    df = load_incremental_files(last_loaded_date)

    df = clean_text_columns(df)
    df = clean_date_columns(df)
    df = clean_datetime_columns(df)

    insert_into_access(df)


if __name__ == "__main__":
    main()