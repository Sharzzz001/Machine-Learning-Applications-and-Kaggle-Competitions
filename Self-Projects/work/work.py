import pyodbc
import pandas as pd
from datetime import datetime

# === Paths ===
access_db_path = r"C:\path\to\your\Database.accdb"
table_name = "DailyOutput"

# === Connect to Access ===
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    rf'DBQ={access_db_path};'
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# === Read today's Excel file ===
today_str = datetime.today().strftime('%Y-%m-%d')
input_file = f'Output1_{today_str}.xlsx'
df_new = pd.read_excel(input_file)
df_new['Date'] = today_str

# === Check if today's date exists in the DB ===
existing_dates = pd.read_sql(f"SELECT DISTINCT Date FROM {table_name}", conn)
if today_str in existing_dates['Date'].astype(str).values:
    confirm = input(f"Data for {today_str} already exists in Access. Overwrite? (y/n): ").lower()
    if confirm == 'y':
        # Delete existing records for today
        cursor.execute(f"DELETE FROM {table_name} WHERE Date = ?", today_str)
        conn.commit()
    else:
        print("Cancelled by user.")
        conn.close()
        exit()

# === Append new data ===
for _, row in df_new.iterrows():
    placeholders = ", ".join(["?"] * len(row))
    sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
    cursor.execute(sql, tuple(row))

conn.commit()
conn.close()
print(f"Data for {today_str} inserted into Access.")