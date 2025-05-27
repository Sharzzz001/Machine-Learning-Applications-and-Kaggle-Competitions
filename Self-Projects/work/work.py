import os
import pandas as pd
import pyodbc
from datetime import datetime, timedelta

# === CONFIG ===
INPUT_FOLDER = r"C:\path\to\input_folder"
ACCESS_DB_PATH = r"C:\path\to\Database.accdb"
TABLE_NAME = "DailyOutput"
FILE_PREFIX = "Output1_"

# === FUNCTIONS ===

def parse_dates(date_input):
    date_input = date_input.replace(' ', '')
    dates = []

    for part in date_input.split(','):
        if '-' in part:
            start_str, end_str = part.split('-')
            start = datetime.strptime(start_str, "%Y%m%d").date()
            end = datetime.strptime(end_str, "%Y%m%d").date()
            dates.extend([start + timedelta(days=i) for i in range((end - start).days + 1)])
        else:
            dates.append(datetime.strptime(part, "%Y%m%d").date())

    return dates

def connect_to_access(db_path):
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        rf'DBQ={db_path};'
    )
    return pyodbc.connect(conn_str)

def process_file_for_date(date, conn):
    file_date_str = date.strftime('%Y-%m-%d')
    access_date_str = date.strftime('%m/%d/%Y')  # Needed for Access match
    filename = f"{FILE_PREFIX}{file_date_str}.xlsx"
    filepath = os.path.join(INPUT_FOLDER, filename)

    if not os.path.exists(filepath):
        print(f"⚠️ File not found: {filename}")
        return

    print(f"\n📄 Processing: {filename}")

    df = pd.read_excel(filepath)
    df["Date"] = access_date_str

    # Replace NaT with None in datetime columns
    datetime_cols = df.select_dtypes(include=['datetime']).columns
    for col in datetime_cols:
        df[col] = df[col].astype('object')
        df[col] = df[col].where(df[col].notna(), None)

    cursor = conn.cursor()

    # Check if date already exists
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE Date = ?", (access_date_str,))
    count = cursor.fetchone()[0]

    if count > 0:
        choice = input(f"⚠️ Data for {file_date_str} already exists. Overwrite? (y/n): ").strip().lower()
        if choice != 'y':
            print("⏭️ Skipping...")
            return
        cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE Date = ?", (access_date_str,))
        conn.commit()
        print("🗑️ Old data deleted.")

    # Prepare insert
    columns = list(df.columns)
    col_names_str = ', '.join(f'[{col}]' for col in columns)
    placeholders = ', '.join(['?'] * len(columns))
    insert_sql = f"INSERT INTO {TABLE_NAME} ({col_names_str}) VALUES ({placeholders})"

    for _, row in df.iterrows():
        cursor.execute(insert_sql, tuple(row))

    conn.commit()
    print(f"✅ Data inserted for {file_date_str}.")

# === MAIN EXECUTION ===

def main():
    user_input = input("📅 Enter date(s) to import (YYYYMMDD, comma-separated or range): ").strip()

    try:
        dates = parse_dates(user_input)
    except ValueError:
        print("❌ Invalid format. Use YYYYMMDD or YYYYMMDD-YYYYMMDD or comma-separated values.")
        return

    try:
        conn = connect_to_access(ACCESS_DB_PATH)
    except Exception as e:
        print(f"❌ Failed to connect to Access DB: {e}")
        return

    for date in dates:
        try:
            process_file_for_date(date, conn)
        except Exception as e:
            print(f"❌ Error processing {date}: {e}")

    conn.close()
    print("\n🎉 All done.")

if __name__ == "__main__":
    main()