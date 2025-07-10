import pandas as pd
import pyodbc
import numpy as np

# ---- CONFIGURATION ---- #
ACCESS_DB_PATH = r"C:\path\to\your\file.accdb"  # 🔁 Change to your Access DB path
TABLE_NAME = "SnapshotTable"  # 🔁 Change to your Access table name
DOC_COMPLETED = "KYC_Completed"
SCREEN_COMPLETED = "Completed"
CANCELLED_KEYWORD = "Cancelled"
START_FROM = 'focus'  # Use 'focus' to start aging from Focus list entering date, or 'snapshot'

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

# ---- REMOVE CANCELLED ACCOUNTS ---- #
cancelled_accounts = df[df['Status'].str.contains(CANCELLED_KEYWORD, case=False, na=False)]['Account number'].unique()
df = df[~df['Account number'].isin(cancelled_accounts)].copy()

# ---- TRUNCATE ON COMPLETION ---- #
def truncate_on_completion(group, status_col, completed_value):
    idx = group[group[status_col] == completed_value].first_valid_index()
    if idx is not None:
        group = group.loc[:idx]
    return group

df_doc = df.groupby('Account number', group_keys=False).apply(
    truncate_on_completion, status_col='Status', completed_value=DOC_COMPLETED
)

df_screen = df.groupby('Account number', group_keys=False).apply(
    truncate_on_completion, status_col='Status_screen', completed_value=SCREEN_COMPLETED
)

# ---- BUSINESS DAY COUNT FUNCTION ---- #
def count_business_days(start, end):
    if pd.isnull(start) or pd.isnull(end):
        return np.nan
    return np.busday_count(start.date(), (end + pd.Timedelta(days=1)).date())

# ---- AGING COMPUTATION FUNCTION ---- #
def compute_aging(group, status_col):
    group = group.sort_values('Date').copy()
    group['prev_status'] = group[status_col].shift()
    group['status_change'] = group[status_col] != group['prev_status']
    group['group_id'] = group['status_change'].cumsum()

    aging = group.groupby('group_id').agg({
        'Date': ['min', 'max'],
        status_col: 'first',
        'Account number': 'first',
        'Focus list entering date': 'first'
    }).reset_index()

    aging.columns = ['group_id', 'Start_Snapshot', 'End_Date', status_col, 'Account number', 'Focus_list_start']

    # Set Start_Date based on switch
    if START_FROM == 'focus':
        aging['Start_Date'] = aging['Start_Snapshot']
        min_group = aging['group_id'].min()
        aging.loc[aging['group_id'] == min_group, 'Start_Date'] = aging.loc[aging['group_id'] == min_group, 'Focus_list_start'].values
    else:
        aging['Start_Date'] = aging['Start_Snapshot']

    aging['Aging_Days'] = aging.apply(lambda row: count_business_days(row['Start_Date'], row['End_Date']), axis=1)

    return aging.drop(columns=['Start_Snapshot', 'Focus_list_start'])

# ---- APPLY AGING ---- #
aging_doc = df_doc.groupby('Account number', group_keys=False).apply(lambda x: compute_aging(x, 'Status'))
aging_screen = df_screen.groupby('Account number', group_keys=False).apply(lambda x: compute_aging(x, 'Status_screen'))

# ---- REMOVE OUTLIERS ---- #
def remove_outliers_iqr(df, col='Aging_Days'):
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    return df[(df[col] >= Q1 - 1.5 * IQR) & (df[col] <= Q3 + 1.5 * IQR)]

aging_doc_filtered = remove_outliers_iqr(aging_doc)
aging_screen_filtered = remove_outliers_iqr(aging_screen)

# ---- OUTPUT ---- #
print("📄 Document Status Aging (Filtered):")
print(aging_doc_filtered.head())

print("\n🔍 Screening Status Aging (Filtered):")
print(aging_screen_filtered.head())


# Get earliest snapshot date available
min_snapshot_date = df['Date'].min()

# Find first non-null focus date per account
first_valid_focus = (
    df.sort_values('Date')
    .dropna(subset=['Focus list entering date'])
    .groupby('Account number')['Focus list entering date']
    .first()
)

# Keep accounts where first valid focus date is >= snapshot start
valid_accounts = first_valid_focus[first_valid_focus >= min_snapshot_date].index

# Filter dataset
df = df[df['Account number'].isin(valid_accounts)].copy()