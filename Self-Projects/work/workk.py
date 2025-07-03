import pandas as pd
import pyodbc
import os

# Your DataFrame
df = pd.DataFrame({
    'ID': [1, 2],
    'Name': ['Alice', 'Bob'],
    'Age': [30, 25],
    'Join_Date': pd.to_datetime(['2022-01-01', '2022-02-01']),
})

# Access DB path (it will be created if not exists)
access_db_path = r'C:\path\to\your\database.accdb'

# If file doesn't exist, create an empty .accdb file (optional)
if not os.path.exists(access_db_path):
    import subprocess
    subprocess.call(['msaccess.exe', '/nostartup', '/compact', access_db_path])

# Connection string
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    rf'DBQ={access_db_path};'
)

# Connect to Access
conn = pyodbc.connect(conn_str, autocommit=True)
cursor = conn.cursor()

# Table name
table_name = 'MyTable'

# Drop table if exists (optional)
try:
    cursor.execute(f"DROP TABLE {table_name}")
except:
    pass

# Create table with appropriate Access data types
column_defs = []
for col in df.columns:
    dtype = df[col].dtype
    if pd.api.types.is_integer_dtype(dtype):
        col_type = 'INT'
    elif pd.api.types.is_float_dtype(dtype):
        col_type = 'DOUBLE'
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        col_type = 'DATETIME'
    else:
        col_type = 'TEXT'
    column_defs.append(f"[{col}] {col_type}")
    
create_table_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
cursor.execute(create_table_sql)

# Insert data row by row
for _, row in df.iterrows():
    placeholders = ', '.join(['?'] * len(df.columns))
    insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
    cursor.execute(insert_sql, tuple(row))

# Clean up
conn.commit()
cursor.close()
conn.close()