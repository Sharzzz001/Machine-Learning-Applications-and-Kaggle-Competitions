import pandas as pd
import numpy as np
from datetime import datetime, date

# Sample input
data = {
    'Title': ['ACC1', 'ACC1', 'ACC1', 'ACC2', 'ACC2'],
    'Review Type': ['TypeA', 'TypeA', 'TypeA', 'TypeB', 'TypeB'],
    'Screening Status': ['Initiated', 'In Progress', 'Completed', 'Initiated', 'Completed'],
    'Document Review Status': ['Initiated', 'In Progress', 'Completed', 'Initiated', 'Completed'],
    'Trigger Date': [date(2024, 6, 1)] * 5,
    'File Date': [date(2024, 6, 1), date(2024, 6, 10), date(2024, 6, 20), date(2024, 6, 5), date(2024, 6, 25)],
    'NS Checker Completion Date': [None, None, date(2024, 6, 25), None, date(2024, 6, 28)],
    'Docs Completion Date': [None, None, date(2024, 6, 22), None, date(2024, 6, 27)],
    'EKYCID': ['EKYC1', 'EKYC1', 'EKYC1', 'EKYC2', 'EKYC2'],
    'Sales Code': ['S001', 'S001', 'S001', 'S002', 'S002'],
    'Maker Name': ['MKR1', 'MKR1', 'MKR1', 'MKR2', 'MKR2'],
    'Checker Name': ['CKR1', 'CKR1', 'CKR1', 'CKR2', 'CKR2']
}
df = pd.DataFrame(data)

# Ensure date columns are date objects
for col in ['Trigger Date', 'File Date', 'NS Checker Completion Date', 'Docs Completion Date']:
    df[col] = pd.to_datetime(df[col], errors='coerce').dt.date

today = date.today()

def business_days_between(start, end):
    if pd.isna(start) or pd.isna(end):
        return 0
    return np.busday_count(start, end)

results = []
group_cols = ['Title', 'Review Type']
df = df.sort_values(by=group_cols + ['File Date'])

for (acct, review_type), group in df.groupby(group_cols):
    group = group.sort_values('File Date')
    prev_doc_status = None
    prev_screen_status = None
    prev_date = None

    # Static columns pulled from last row in group
    static_cols = group[['EKYCID', 'Sales Code', 'Maker Name', 'Checker Name']].iloc[-1].to_dict()

    for idx, row in group.iterrows():
        file_date = row['File Date']
        trigger_date = row['Trigger Date'] or file_date

        # --- DOC Review Process ---
        doc_status = row['Document Review Status']
        if doc_status != prev_doc_status:
            start_date = prev_date or trigger_date
            end_date = (
                row['Docs Completion Date']
                if str(doc_status).lower() == 'completed'
                else file_date or today
            ) or today

            if prev_doc_status:
                results.append({
                    'Title': acct,
                    'Review Type': review_type,
                    'Process': 'Doc Review',
                    'Status': prev_doc_status,
                    'Days': business_days_between(start_date, end_date),
                    **static_cols
                })
            prev_doc_status = doc_status

        # --- Screening Process ---
        screen_status = row['Screening Status']
        if screen_status != prev_screen_status:
            start_date = prev_date or trigger_date
            end_date = (
                row['NS Checker Completion Date']
                if str(screen_status).lower() == 'completed'
                else file_date or today
            ) or today

            if prev_screen_status:
                results.append({
                    'Title': acct,
                    'Review Type': review_type,
                    'Process': 'Screening',
                    'Status': prev_screen_status,
                    'Days': business_days_between(start_date, end_date),
                    **static_cols
                })
            prev_screen_status = screen_status

        prev_date = file_date

# Final DataFrame
result_df = pd.DataFrame(results)
print(result_df)