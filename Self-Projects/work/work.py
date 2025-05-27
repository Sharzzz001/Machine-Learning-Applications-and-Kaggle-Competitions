import os
import sys
import argparse
import pandas as pd
import pyodbc
from datetime import datetime, timedelta

# === CONFIGURABLE SETTINGS ===
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
            start = datetime.strptime(start_str, "%Y-%m-%d").date()
            end = datetime.strptime(end_str, "%Y-%m-%d").date()
            dates.extend([start + timedelta(days=i) for i in range((end - start).days + 1)])
        else:
            dates.append(datetime.strptime(part, "%Y-%m-%d").date())
    return dates

def connect_to_access(db_path):
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        rf'DBQ={db_path};'
    )
    return pyodbc.connect(conn_str)

def process_file_for_date(date, conn):
    file_date_str = date.strftime('%Y-%m-%d')
    access_date_str = date.strftime('%m/%d/%Y')
    filename = f"{FILE_PREFIX}{file_date_str}.xlsx"
    filepath = os.path.join(INPUT_FOLDER, filename)

    if not os.path.exists(filepath):
        print(f"⚠️ File not found: {filename}")
        return

    print(f"📄 Processing file: {filename}")

    df = pd.read_excel(filepath)
    df["Date"] = access_date_str

    # Convert NaT to None in datetime columns
    datetime_cols = df.select_dtypes(include=['datetime']).columns
    for col in datetime_cols:
        df[col] = df[col].astype("object")
        df[col] = df[col].where(df[col].notna(), None)

    cursor = conn.cursor()

    # Check for existing data
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE Date = ?", (access_date_str,))
    count = cursor.fetchone()[0]

    if count > 0:
        choice = input(f"⚠️ Data for {file_date_str} exists. Overwrite? (y/n): ").strip().lower()
        if choice != 'y':
            print(f"⏭️ Skipped {file_date_str}")
            return
        cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE Date = ?", (access_date_str,))
        conn.commit()
        print(f"🗑️ Existing data for {file_date_str} deleted.")

    # Insert new data
    columns = list(df.columns)
    col_names_str = ', '.join(f'[{col}]' for col in columns)
    placeholders = ', '.join(['?'] * len(columns))
    insert_sql = f"INSERT INTO {TABLE_NAME} ({col_names_str}) VALUES ({placeholders})"

    for _, row in df.iterrows():
        cursor.execute(insert_sql, tuple(row))
    
    conn.commit()
    print(f"✅ Inserted data for {file_date_str}.")

# === MAIN ===
def main():
    parser = argparse.ArgumentParser(description="Import Excel files to Access DB by date")
    parser.add_argument(
        "--dates",
        required=True,
        help="Date(s) to import. Example: 2025-05-25 or 2025-05-25,2025-05-27 or 2025-05-25 - 2025-05-28"
    )
    args = parser.parse_args()

    try:
        dates = parse_dates(args.dates)
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD or comma-separated/range.")
        sys.exit(1)

    try:
        conn = connect_to_access(ACCESS_DB_PATH)
    except Exception as e:
        print(f"❌ Could not connect to Access DB: {e}")
        sys.exit(1)

    for date in dates:
        try:
            process_file_for_date(date, conn)
        except Exception as e:
            print(f"❌ Error processing {date}: {e}")

    conn.close()
    print("🎉 All done.")

if __name__ == "__main__":
    main()