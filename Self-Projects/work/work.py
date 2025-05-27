import pyodbc
import pandas as pd

# Path to your Access database
access_db_path = r"C:\path\to\your\Database.accdb"

# Connect using ODBC
conn_str = (
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    rf"DBQ={access_db_path};"
)
conn = pyodbc.connect(conn_str)

# === Example 1: Run saved query ===
query_name = "YourSavedQuery"
df1 = pd.read_sql(f"SELECT * FROM [{query_name}]", conn)

# === Example 2: Run ad-hoc SQL ===
sql_query = "SELECT TOP 10 * FROM Orders WHERE Status = 'Pending'"
df2 = pd.read_sql(sql_query, conn)

conn.close()

# Display result
print(df1.head())