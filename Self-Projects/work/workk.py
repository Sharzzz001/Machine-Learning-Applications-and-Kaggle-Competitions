import pyodbc
import pandas as pd
import numpy as np
from datetime import datetime

# === CONFIGURATION ===
db_path = r'C:\Path\To\Your\Database.accdb'  # <--- Change this to your path
table_name = 'Snapshots'                     # <--- Your Access table name
account_id_filter = 123                      # <--- Account ID to filter
review_type_filter = 'RR'                    # <--- Review Type to filter
today = pd.to_datetime('2025-07-25')         # <--- Change to today’s date or use datetime.today()

# === ACCESS CONNECTION ===
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    rf'DBQ={db_path};'
)

conn = pyodbc.connect(conn_str)

# === READ DATA FROM ACCESS ===
query = f"""
SELECT 
    [Account ID], 
    [Review Type], 
    [Screening Status], 
    [Doc Review], 
    [Trigger Date], 
    [File Date]
FROM {table_name}
WHERE 
    [Account ID] = {account_id_filter}
    AND [Review Type] = '{review_type_filter}'
"""

df = pd.read_sql(query, conn)

# === CLEANING COLUMNS ===
df = df.rename(columns={
    'Account ID': 'Account_ID',
    'Review Type': 'Review_Type',
    'Screening Status': 'Screening_Status',
    'Doc Review': 'Doc_Status',
    'Trigger Date': 'Trigger_Date',
    'File Date': 'File_Date'
})

df['Trigger_Date'] = pd.to_datetime(df['Trigger_Date'])
df['File_Date'] = pd.to_datetime(df['File_Date'])

# === AGING CALCULATION FUNCTION ===
def calculate_aging(group_df, status_col, process_name):
    statuses = group_df[[status_col, 'Trigger_Date', 'File_Date']].copy()
    statuses = statuses.sort_values('File_Date')
    
    statuses['Prev_Status'] = statuses[status_col].shift(1)
    statuses['Change'] = statuses[status_col] != statuses['Prev_Status']
    statuses.loc[statuses.index[0], 'Change'] = True  # Force first row as change

    # Start dates
    start_dates = []
    for idx, row in statuses.iterrows():
        if row['Change']:
            if idx == statuses.index[0]:
                start_dates.append(row['Trigger_Date'])
            else:
                start_dates.append(row['File_Date'])
        else:
            start_dates.append(np.nan)

    statuses['Start_Date'] = start_dates
    statuses['Start_Date'].ffill(inplace=True)

    # End dates
    statuses['End_Date'] = statuses['File_Date'].shift(-1)
    statuses['End_Date'].fillna(today, inplace=True)

    # Only keep change points
    changed = statuses[statuses['Change']]

    # Calculate business days, minimum 1 day
    changed['Days'] = changed.apply(
        lambda row: max(1, np.busday_count(row['Start_Date'].date(), row['End_Date'].date())),
        axis=1
    )

    # Prepare result
    records = []
    for _, row in changed.iterrows():
        records.append({
            'Process': process_name,
            'Status': row[status_col],
            'Days': row['Days']
        })

    return records

# === MAIN LOOP ===
results = []

# Group by Account_ID + Review_Type (single account in this case but scalable)
for (acc_id, rev_type), group in df.groupby(['Account_ID', 'Review_Type']):
    
    # Screening Status Aging
    screening_results = calculate_aging(group, 'Screening_Status', 'Screening')
    for r in screening_results:
        r['Account_ID'] = acc_id
        r['Review_Type'] = rev_type
        results.append(r)
    
    # Doc Review Status Aging
    doc_results = calculate_aging(group, 'Doc_Status', 'Doc Review')
    for r in doc_results:
        r['Account_ID'] = acc_id
        r['Review_Type'] = rev_type
        results.append(r)

# === OUTPUT ===
result_df = pd.DataFrame(results)

# Reorder columns
result_df = result_df[['Account_ID', 'Review_Type', 'Process', 'Status', 'Days']]

print(result_df)