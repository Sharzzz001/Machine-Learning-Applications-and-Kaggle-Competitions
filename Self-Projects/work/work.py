import os
import pandas as pd
import pyodbc
from datetime import datetime

# === Configuration ===
input_folder = r'C:\path\to\input_folder'
access_db_path = r'C:\path\to\Database.accdb'
table_name = 'DailyOutput'
file_prefix = 'Output1_'

# === Today's Date Info ===
today = datetime.today()
today_str_file = today.strftime('%Y-%m-%d')
today_str_access = today.strftime('%m/%d/%Y')

# === Build filename and path ===
expected_filename = f'{file_prefix}{today_str_file}.xlsx'
expected_filepath = os.path.join(input_folder, expected_filename)

if not os.path.exists(expected_filepath):
    print(f"❌ No file found: {expected_filename}")
    exit()

# === Read today's Excel file ===
df = pd.read_excel(expected_filepath)

# === Add 'Date' column ===
df['Date'] = today_str_access

# === Connect to Access DB ===
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    rf'DBQ={access_db_path};'
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# === Check if today's data already exists ===
check_sql = f"SELECT COUNT(*) FROM {table_name} WHERE Date = ?"
cursor.execute(check_sql, (today_str_access,))
count = cursor.fetchone()[0]

if count > 0:
    confirm = input(f"⚠️ Data for {today_str_file} already exists. Overwrite? (y/n): ").lower()
    if confirm != 'y':
        print("❌ Operation cancelled.")
        conn.close()
        exit()
    # Delete existing rows for today
    delete_sql = f"DELETE FROM {table_name} WHERE Date = ?"
    cursor.execute(delete_sql, (today_str_access,))
    conn.commit()
    print(f"✅ Existing data for {today_str_file} deleted.")

# === Prepare Insert ===
columns = list(df.columns)  # Ensure this matches Access table columns
col_placeholder = ', '.join(['?'] * len(columns))
col_names_str = ', '.join(columns)
insert_sql = f"INSERT INTO {table_name} ({col_names_str}) VALUES ({col_placeholder})"

# === Insert Data Row-by-Row ===
for _, row in df.iterrows():
    cursor.execute(insert_sql, tuple(row))

conn.commit()
conn.close()
print(f"✅ Data from {expected_filename} successfully inserted into Access table '{table_name}'.")