import os
import re
from datetime import datetime
import pandas as pd
import pyodbc

# --- CONFIGURATION ---
ACCESS_DB_PATH = r"C:\path\to\RR_Request_DB.accdb"
SNAPSHOT_FOLDER = r"C:\path\to\snapshots"
TABLE_NAME = "Snapshots"

# ✅ ONLY THESE 30 COLUMNS WILL BE IMPORTED
# Define column names and their Access data types (file_date included)
COLUMNS_AND_TYPES = {
    "Title": "TEXT(255)",
    "Review Type": "TEXT(255)",
    "Assigned To": "TEXT(255)",
    "Checker Name": "TEXT(255)",
    "Trigger Date": "DATE",
    "Screenings": "TEXT(255)",
    "Documents Ready for Review": "TEXT(255)",
    # Add the remaining ~23 columns here:
    "Status": "TEXT(255)",
    "Request Date": "DATE",
    "Checker Completion Date": "DATE",
    # ...
    # (up to your desired 30 columns)
    "file_date": "DATE"  # This is always added automatically
}

# --- Extract file_date from filename ---
def extract_file_date(filename):
    match = re.search(r'RR_Request_(\d{4}-\d{2}-\d{2})\.xlsx', filename)
    return datetime.strptime(match.group(1), "%Y-%m-%d").date() if match else None

# --- Get sorted list of Excel files ---
def get_excel_files_sorted(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith(".xlsx") and "RR_Request_" in f]
    return sorted(files, key=lambda x: extract_file_date(x) or datetime.min.date())

# --- Connect to Access DB ---
def connect_access_db(db_path):
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        rf"DBQ={db_path};"
    )
    return pyodbc.connect(conn_str)

# --- Create table if it doesn't exist ---
def ensure_table_exists(cursor, table_name, col_types):
    cursor.execute(f"""
        SELECT COUNT(*) FROM MSysObjects
        WHERE Name='{table_name}' AND Type=1;
    """)
    if cursor.fetchone()[0] == 0:
        col_defs = ", ".join([f"[{col}] {dtype}" for col, dtype in col_types.items()])
        create_sql = f"CREATE TABLE [{table_name}] ({col_defs});"
        cursor.execute(create_sql)
        print(f"✅ Created table '{table_name}' with {len(col_types)} columns.")

# --- Main processing function ---
def import_snapshots_to_access(folder_path, db_path, table_name, col_types):
    conn = connect_access_db(db_path)
    cursor = conn.cursor()
    ensure_table_exists(cursor, table_name, col_types)

    for file in get_excel_files_sorted(folder_path):
        file_path = os.path.join(folder_path, file)
        file_date = extract_file_date(file)
        if not file_date:
            print(f"⚠️ Skipping invalid filename: {file}")
            continue

        print(f"\n📄 Processing: {file} (file_date: {file_date})")

        try:
            df_raw = pd.read_excel(file_path, dtype=object)  # Read everything as text/object
            df_raw.columns = [c.strip() for c in df_raw.columns]
        except Exception as e:
            print(f"❌ Could not read {file}: {e}")
            continue

        expected_cols = list(col_types.keys())
        expected_cols.remove("file_date")  # We will add it manually
        missing = set(expected_cols) - set(df_raw.columns)
        if missing:
            print(f"❌ Missing columns in {file}: {missing}")
            continue

        df = df_raw[expected_cols].copy()
        df["file_date"] = file_date

        # Convert datetime-like columns to datetime.date
        datetime_cols = [col for col in expected_cols if col_types[col] == "DATE"]
        for col in datetime_cols:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

        df = df.dropna(subset=["file_date"])

        # Delete existing rows for the same file_date
        try:
            cursor.execute(f"DELETE FROM [{table_name}] WHERE file_date = ?", file_date)
            conn.commit()
            print(f"🗑️  Deleted old rows for file_date = {file_date}")
        except Exception as e:
            print(f"❌ Failed to delete old rows for {file_date}: {e}")
            continue

        # Insert new rows
        insert_cols = list(col_types.keys())
        placeholders = ", ".join(["?"] * len(insert_cols))
        col_names = ", ".join(f"[{col}]" for col in insert_cols)
        insert_sql = f"INSERT INTO [{table_name}] ({col_names}) VALUES ({placeholders})"

        inserted = 0
        for _, row in df.iterrows():
            try:
                values = [row.get(col, None) for col in insert_cols]
                cursor.execute(insert_sql, values)
                inserted += 1
            except Exception as e:
                print(f"❌ Row insert error (Title={row.get('Title')}): {e}")

        conn.commit()
        print(f"✅ Inserted {inserted} rows for {file_date}")

    cursor.close()
    conn.close()
    
import_snapshots_to_access(
    folder_path=SNAPSHOT_FOLDER,
    db_path=ACCESS_DB_PATH,
    table_name=TABLE_NAME,
    col_types=COLUMNS_AND_TYPES
)