import pyodbc
import pandas as pd
import numpy as np
from datetime import datetime

# === CONFIGURATION ===
db_path = r'C:\Path\To\Your\Database.accdb'  # <-- Update your path
table_name = 'Snapshots'                     # <-- Your Access table name
today = pd.to_datetime('2025-07-25')         # <-- Or use pd.to_datetime(datetime.today())

# === ACCESS CONNECTION ===
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    rf'DBQ={db_path};'
)

conn = pyodbc.connect(conn_str)

# === READ FULL DATA FROM ACCESS ===
query = f"""
SELECT 
    [Account ID], 
    [Review Type], 
    [Screening Status], 
    [Doc Review], 
    [Trigger Date], 
    [File Date]
FROM {table_name}
"""

df = pd.read_sql(query, conn)

# === CLEAN COLUMNS ===
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
def calculate_aging(group_df, status_col, process_name, today):
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

    # Calculate business days with minimum 1 day aging
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

# Group by Account_ID + Review_Type
for (acc_id, rev_type), group in df.groupby(['Account_ID', 'Review_Type']):
    
    # Screening Status Aging
    screening_results = calculate_aging(group, 'Screening_Status', 'Screening', today)
    for r in screening_results:
        r['Account_ID'] = acc_id
        r['Review_Type'] = rev_type
        results.append(r)
    
    # Doc Review Status Aging
    doc_results = calculate_aging(group, 'Doc_Status', 'Doc Review', today)
    for r in doc_results:
        r['Account_ID'] = acc_id
        r['Review_Type'] = rev_type
        results.append(r)

# === CREATE RESULT DATAFRAME ===
result_df = pd.DataFrame(results)

# Reorder columns
result_df = result_df[['Account_ID', 'Review_Type', 'Process', 'Status', 'Days']]

# === ADD TOTAL AGING COLUMNS ===
result_df['Total_Doc_Aging'] = 0
result_df['Total_NS_Aging'] = 0

# Compute total aging per Account_ID + Review_Type
grouped = result_df.groupby(['Account_ID', 'Review_Type'])

for (acc_id, rev_type), group in grouped:
    total_doc = group.loc[group['Process'] == 'Doc Review', 'Days'].sum()
    total_ns = group.loc[group['Process'] == 'Screening', 'Days'].sum()
    
    # Apply totals back to each row in the group
    result_df.loc[
        (result_df['Account_ID'] == acc_id) & (result_df['Review_Type'] == rev_type), 
        'Total_Doc_Aging'
    ] = total_doc
    
    result_df.loc[
        (result_df['Account_ID'] == acc_id) & (result_df['Review_Type'] == rev_type), 
        'Total_NS_Aging'
    ] = total_ns

# === OUTPUT ===
print(result_df)