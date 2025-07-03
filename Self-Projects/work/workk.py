import pandas as pd
import pyodbc
import os

# Sample DataFrame (replace with your actual df)
df = pd.DataFrame({
    'ID': pd.Series(dtype='int'),
    'Name': pd.Series(dtype='str'),
    'Age': pd.Series(dtype='float'),
    'Join_Date': pd.Series(dtype='datetime64[ns]'),
})

# Path to Access .accdb file
access_db_path = r'C:\path\to\your\database.accdb'

# Ensure the file exists (Access doesn't allow creating new .accdb via pyodbc)
if not os.path.exists(access_db_path):
    raise FileNotFoundError(f"Access DB not found at: {access_db_path}. Please create a blank .accdb file manually.")

# pyodbc connection string
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    rf'DBQ={access_db_path};'
)

# Connect to Access
conn = pyodbc.connect(conn_str, autocommit=True)
cursor = conn.cursor()

# Table name
table_name = 'MyEmptyTable'

# Drop table if exists
try:
    cursor.execute(f"DROP TABLE [{table_name}]")
except:
    pass

# Map pandas dtypes to Access types
type_map = {
    'int64': 'INT',
    'float64': 'DOUBLE',
    'object': 'TEXT',
    'datetime64[ns]': 'DATETIME',
    'bool': 'YESNO'
}

column_defs = []
for col in df.columns:
    dtype_str = str(df[col].dtype)
    access_type = type_map.get(dtype_str, 'TEXT')  # Default to TEXT if unknown
    column_defs.append(f"[{col}] {access_type}")

# Create table
create_sql = f"CREATE TABLE [{table_name}] ({', '.join(column_defs)})"
cursor.execute(create_sql)

# Done
cursor.close()
conn.close()
print(f"Table '{table_name}' created successfully in {access_db_path}")