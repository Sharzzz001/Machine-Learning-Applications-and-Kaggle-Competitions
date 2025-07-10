import pandas as pd
import pyodbc
import seaborn as sns
import matplotlib.pyplot as plt

# Path to your .accdb file
access_db_path = r'C:\path\to\your\database.accdb'  # CHANGE THIS

# Connect to Access DB
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    rf'DBQ={access_db_path};'
)
conn = pyodbc.connect(conn_str)

# Load snapshot table
df = pd.read_sql("SELECT * FROM SnapshotTable", conn)  # CHANGE TABLE NAME
df['Date'] = pd.to_datetime(df['Date'])
df['Focus list entering date'] = pd.to_datetime(df['Focus list entering date'], errors='coerce')


df = df.sort_values(by=['Account number', 'Date'])


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

aging_doc = df.groupby('Account number', group_keys=False).apply(lambda x: compute_aging(x, 'Status'))
aging_screen = df.groupby('Account number', group_keys=False).apply(lambda x: compute_aging(x, 'Status_screen'))


def remove_outliers_iqr(df, col='Aging_Days'):
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    return df[(df[col] >= Q1 - 1.5 * IQR) & (df[col] <= Q3 + 1.5 * IQR)]

aging_doc_filtered = remove_outliers_iqr(aging_doc)
aging_screen_filtered = remove_outliers_iqr(aging_screen)



avg_doc = aging_doc_filtered.groupby('Status')['Aging_Days'].mean().reset_index()
avg_screen = aging_screen_filtered.groupby('Status_screen')['Aging_Days'].mean().reset_index()



plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
sns.boxplot(data=aging_doc_filtered, x='Status', y='Aging_Days')
plt.xticks(rotation=45)
plt.title("Document Review Status Aging")

plt.subplot(1, 2, 2)
sns.boxplot(data=aging_screen_filtered, x='Status_screen', y='Aging_Days')
plt.xticks(rotation=45)
plt.title("Name Screening Status Aging")

plt.tight_layout()
plt.show()


avg_doc.to_excel("avg_document_status_aging.xlsx", index=False)
avg_screen.to_excel("avg_screening_status_aging.xlsx", index=False)