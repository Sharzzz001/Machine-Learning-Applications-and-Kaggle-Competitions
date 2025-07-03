import os
import re
from datetime import datetime
import pandas as pd
import pyodbc

# --- Extract date from filename ---
def extract_file_date(filename):
    match = re.search(r'RR_Request_(\d{4}-\d{2}-\d{2})\.xlsx', filename)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()
    return None

# --- List and sort files by snapshot date ---
def get_excel_files_sorted(folder_path):
    files = [
        f for f in os.listdir(folder_path)
        if f.endswith('.xlsx') and 'RR_Request_' in f
    ]
    return sorted(files, key=lambda f: extract_file_date(f))

# --- Connect to Access DB ---
def connect_access_db(db_path):
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        rf'DBQ={db_path};'
    )
    return pyodbc.connect(conn_str)

# --- Get already-imported snapshot dates ---
def get_existing_file_dates(cursor, table_name):
    try:
        cursor.execute(f"SELECT DISTINCT file_date FROM {table_name}")
        return {row[0] for row in cursor.fetchall()}
    except:
        return set()

# --- Get already-inserted primary keys to avoid duplicates ---
def get_existing_keys(cursor, table_name):
    try:
        cursor.execute(f"SELECT Title, [Review Type], file_date FROM {table_name}")
        return {(row[0], row[1], row[2]) for row in cursor.fetchall()}
    except:
        return set()

# --- Merge new snapshots to Access DB ---
def merge_snapshots_to_access(folder_path, db_path, table_name='Snapshots'):
    conn = connect_access_db(db_path)
    cursor = conn.cursor()

    existing_dates = get_existing_file_dates(cursor, table_name)
    existing_keys = get_existing_keys(cursor, table_name)
    new_files_added = False

    for file in get_excel_files_sorted(folder_path):
        file_date = extract_file_date(file)
        if file_date is None or file_date in existing_dates:
            continue  # Already imported

        df = pd.read_excel(os.path.join(folder_path, file))
        df.columns = [c.strip() for c in df.columns]  # Clean column names
        df['file_date'] = file_date

        # Ensure 'Review Type' is present (if column name varies, fix here)
        if 'Review Type' not in df.columns:
            print(f"Missing 'Review Type' in {file}")
            continue

        # Create table if not exists
        try:
            cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
        except:
            col_defs = ", ".join(
                f"[{col}] TEXT" if col != "file_date" else "[file_date] DATE"
                for col in df.columns
            )
            create_sql = f"CREATE TABLE {table_name} ({col_defs})"
            cursor.execute(create_sql)

        # Insert rows, avoiding duplicates by (Title, Review Type, file_date)
        for _, row in df.iterrows():
            key = (row['Title'], row['Review Type'], file_date)
            if key in existing_keys:
                continue

            placeholders = ", ".join("?" for _ in row)
            columns = ", ".join(f"[{col}]" for col in df.columns)
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

            try:
                cursor.execute(sql, tuple(row))
                existing_keys.add(key)
            except Exception as e:
                print(f"Error inserting row for {key}: {e}")

        conn.commit()
        print(f"✔ Imported snapshot: {file_date}")
        new_files_added = True

    cursor.close()
    conn.close()
    return new_files_added