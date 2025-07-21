import pandas as pd
import numpy as np
from datetime import datetime

# Sample data
data = [
    [123, 'Ready for Name Screening', 'Pending RM', '2025-07-14', '2025-07-18'],
    [123, 'Pending CDD', 'Pending RM', '2025-07-14', '2025-07-21'],
    [123, 'Pending RM', 'Pending CDD', '2025-07-14', '2025-07-22']
]

df = pd.DataFrame(data, columns=['Account_ID', 'Screening_Status', 'Doc_Status', 'Trigger_Date', 'File_Date'])
df['Trigger_Date'] = pd.to_datetime(df['Trigger_Date'])
df['File_Date'] = pd.to_datetime(df['File_Date'])

today = pd.to_datetime('2025-07-25')

results = []

for process in ['Screening_Status', 'Doc_Status']:
    for acc_id, group in df.groupby('Account_ID'):
        statuses = group[[process, 'Trigger_Date', 'File_Date']].copy()
        statuses = statuses.sort_values('File_Date')
        
        # Track changes
        statuses['Prev_Status'] = statuses[process].shift(1)
        statuses['Change'] = statuses[process] != statuses['Prev_Status']
        statuses.loc[statuses.index[0], 'Change'] = True  # Force first row as change

        # Determine start dates
        start_dates = []
        for idx, row in statuses.iterrows():
            if row['Change']:
                if idx == statuses.index[0]:
                    start_dates.append(row['Trigger_Date'])  # First status uses Trigger Date
                else:
                    start_dates.append(row['File_Date'])
            else:
                start_dates.append(np.nan)

        statuses['Start_Date'] = start_dates
        statuses['Start_Date'].ffill(inplace=True)

        # Determine end dates
        statuses['End_Date'] = statuses['File_Date'].shift(-1)
        statuses['End_Date'].fillna(today, inplace=True)

        # Only keep changes
        changed_statuses = statuses[statuses['Change']]
        
        # Calculate business days
        changed_statuses['Days'] = changed_statuses.apply(
            lambda row: np.busday_count(row['Start_Date'].date(), row['End_Date'].date()),
            axis=1
        )
        
        for _, row in changed_statuses.iterrows():
            results.append({
                'Account_ID': acc_id,
                'Process': 'Screening' if process == 'Screening_Status' else 'Doc Review',
                'Status': row[process],
                'Days': row['Days']
            })

result_df = pd.DataFrame(results)
print(result_df)

import pyodbc
import pandas as pd

# DB Path
db_path = r'C:\Path\To\Your\Database.accdb'

# Connection
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    rf'DBQ={db_path};'
)

conn = pyodbc.connect(conn_str)

# Query
query = """
SELECT Account_ID, Screening_Status, Doc_Status, Trigger_Date, File_Date
FROM Snapshots
"""

# Read into DataFrame
df = pd.read_sql(query, conn)

# Date conversion
df['Trigger_Date'] = pd.to_datetime(df['Trigger_Date'])
df['File_Date'] = pd.to_datetime(df['File_Date'])

print(df.head())
