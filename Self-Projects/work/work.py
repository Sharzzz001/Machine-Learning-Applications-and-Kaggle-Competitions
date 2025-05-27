import pyodbc
import pandas as pd
from replicate_aging_queries import create_final_aging_table

# MS Access database path
access_db_path = r'C:\path\to\your\database.accdb'

# Connection string for Access DB (adjust if .mdb)
conn_str = (
    r'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};'
    r'DBQ={};'.format(access_db_path)
)

# Connect to Access DB
conn = pyodbc.connect(conn_str)

# Read entire Aging_Table
aging_df = pd.read_sql("SELECT * FROM Aging_Table", conn)

# Read Bin table (Status -> Doc_Status)
bin_df = pd.read_sql("SELECT * FROM Bin_Table", conn)

# Read Bin1 table (Status_screening -> NS_Status)
bin1_df = pd.read_sql("SELECT * FROM Bin_Table1", conn)

conn.close()

# Run the replicate aging queries script function
final_aging_df = create_final_aging_table(aging_df, bin_df, bin1_df)

# View result
print(final_aging_df.head())

# Optionally save to Excel
# final_aging_df.to_excel('Final_Aging_Result.xlsx', index=False)