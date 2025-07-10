import pandas as pd
import pyodbc
import numpy as np

# ---- CONFIGURATION ---- #
ACCESS_DB_PATH = r"C:\path\to\your\file.accdb"  # 🔁 Change this
TABLE_NAME = "SnapshotTable"  # 🔁 Change this
STATUS_COMPLETE = "KYC_Completed"
SCREEN_COMPLETE = "Completed"
CUTOFF_DATE = pd.to_datetime("2021-03-01")  # 🔁 User input
CANCELLED_KEYWORD = "Cancelled"

# ---- CONNECT TO ACCESS ---- #
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    rf'DBQ={ACCESS_DB_PATH};'
)
conn = pyodbc.connect(conn_str)
df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
conn.close()

# ---- PREPROCESSING ---- #
df['Date'] = pd.to_datetime(df['Date'])
df['Focus list entering date'] = pd.to_datetime(df['Focus list entering date'], errors='coerce')

# ---- FILTER BY CUTOFF DATE ---- #
df = df[df['Focus list entering date'] >= CUTOFF_DATE].copy()

# ---- REMOVE CANCELLED ACCOUNTS ---- #
cancelled_accounts = df[df['Status'].str.contains(CANCELLED_KEYWORD, case=False, na=False)]['Account number'].unique()
df = df[~df['Account number'].isin(cancelled_accounts)].copy()

# ---- FUNCTION: TRUNCATE AT FIRST COMPLETED STATUS ---- #
def truncate_at_completion(group, status_col, completed_value):
    group = group.sort_values('Date')
    idx = group[group[status_col] == completed_value].first_valid_index()
    if idx is not None:
        group = group.loc[:idx]  # Include the row with completed status
    return group

df_doc = df.groupby('Account number', group_keys=False).apply(
    truncate_at_completion, status_col='Status', completed_value=STATUS_COMPLETE
)

df_screen = df.groupby('Account number', group_keys=False).apply(
    truncate_at_completion, status_col='Status_screen', completed_value=SCREEN_COMPLETE
)

# ---- FUNCTION: BUSINESS DAY AGING ---- #
def compute_aging_business_days(group, status_col):
    group = group.sort_values('Date')
    start_date = group['Date'].min()
    end_date = group['Date'].max()
    status = group[status_col].iloc[-1]
    acc = group['Account number'].iloc[0]
    days = np.busday_count(start_date.date(), (end_date + pd.Timedelta(days=1)).date())
    return pd.Series({
        'Account number': acc,
        status_col: status,
        'Start_Date': start_date,
        'End_Date': end_date,
        'Aging_Days': days
    })

# ---- APPLY ---- #
aging_doc = df_doc.groupby('Account number', group_keys=False).apply(lambda x: compute_aging_business_days(x, 'Status'))
aging_screen = df_screen.groupby('Account number', group_keys=False).apply(lambda x: compute_aging_business_days(x, 'Status_screen'))

# ---- OUTPUT ---- #
print("📄 Document Status Aging:")
print(aging_doc.head())

print("\n🔍 Screening Status Aging:")
print(aging_screen.head())