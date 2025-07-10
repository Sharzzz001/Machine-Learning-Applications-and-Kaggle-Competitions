import pandas as pd
import pyodbc

# ---- CONFIGURATION ---- #
ACCESS_DB_PATH = r"C:\path\to\your\file.accdb"  # Change this
TABLE_NAME = "SnapshotTable"  # Change this
DOC_COMPLETED = "KYC_Completed"
SCREEN_COMPLETED = "Completed"
CANCELLED_KEYWORD = "Cancelled"

# ---- CONNECT TO ACCESS ---- #
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    rf'DBQ={ACCESS_DB_PATH};'
)
conn = pyodbc.connect(conn_str)
df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
conn.close()

# ---- CLEANING ---- #
df['Date'] = pd.to_datetime(df['Date'])
df['Focus list entering date'] = pd.to_datetime(df['Focus list entering date'], errors='coerce')

# Remove cancelled accounts
cancelled_accounts = df[df['Status'].str.contains(CANCELLED_KEYWORD, case=False, na=False)]['Account number'].unique()
df = df[~df['Account number'].isin(cancelled_accounts)].copy()

# ---- TRUNCATE ON COMPLETION ---- #
def truncate_on_completion(group, status_col, completed_value):
    idx = group[group[status_col] == completed_value].first_valid_index()
    if idx is not None:
        group = group.loc[:idx]  # include the completion day
    return group

# Truncate Status
df_doc = df.groupby('Account number', group_keys=False).apply(
    truncate_on_completion, status_col='Status', completed_value=DOC_COMPLETED
)

# Truncate Status_screen
df_screen = df.groupby('Account number', group_keys=False).apply(
    truncate_on_completion, status_col='Status_screen', completed_value=SCREEN_COMPLETED
)

# ---- AGING CALCULATION FUNCTION ---- #
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

    # Start aging from Focus list entering date for the first group only
    aging['Start_Date'] = aging['Start_Snapshot']
    min_group = aging['group_id'].min()
    aging.loc[aging['group_id'] == min_group, 'Start_Date'] = aging.loc[aging['group_id'] == min_group, 'Focus_list_start'].values

    aging['Aging_Days'] = (aging['End_Date'] - aging['Start_Date']).dt.days + 1
    return aging.drop(columns=['Start_Snapshot', 'Focus_list_start'])

# ---- APPLY TO BOTH PROCESSES ---- #
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

# ---- DONE ---- #
print("Filtered Document Aging Sample:")
print(aging_doc_filtered.head())

print("\nFiltered Screening Aging Sample:")
print(aging_screen_filtered.head())

def truncate_on_completion(group, status_col, completion_value):
    idx = group[group[status_col] == completion_value].first_valid_index()
    if idx is not None:
        group = group.loc[:idx]  # Include the completion day
    return group

df_doc = df_clean.groupby('Account number', group_keys=False).apply(
    truncate_on_completion, status_col='Status', completion_value='KYC_Completed'
)

df_screen = df_clean.groupby('Account number', group_keys=False).apply(
    truncate_on_completion, status_col='Status_screen', completion_value='Completed'
)

def compute_aging(group, status_col):
    group = group.copy()
    group['prev_status'] = group[status_col].shift()
    group['status_change'] = group[status_col] != group['prev_status']
    group['group_id'] = group['status_change'].cumsum()
    aging = group.groupby('group_id').agg({
        'Date': ['min', 'max'],
        status_col: 'first',
        'Account number': 'first'
    }).reset_index()

    aging.columns = ['group_id', 'Start_Date', 'End_Date', status_col, 'Account number']
    aging['Aging_Days'] = (aging['End_Date'] - aging['Start_Date']).dt.days + 1
    return aging

aging_doc = df_doc.groupby('Account number', group_keys=False).apply(lambda x: compute_aging(x, 'Status'))
aging_screen = df_screen.groupby('Account number', group_keys=False).apply(lambda x: compute_aging(x, 'Status_screen'))




