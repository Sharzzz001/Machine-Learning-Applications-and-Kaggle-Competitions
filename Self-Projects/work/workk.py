import pandas as pd
from datetime import datetime, date
import numpy as np

# Sample Data – replace this with your actual SharePoint-snapshot-concatenated DataFrame
sample_data = {
    'AccountNumber': ['A1', 'A1', 'A1', 'A2', 'A2'],
    'Review Type': ['Annual', 'Annual', 'Annual', 'Quarterly', 'Quarterly'],
    'Screening Status': ['Initiated', 'In Progress', 'Completed', 'Initiated', 'Completed'],
    'Document Review Status': ['Initiated', 'In Progress', 'Completed', 'Initiated', 'Completed'],
    'Trigger Date': [date(2024, 1, 1)] * 5,
    'File Date': [date(2024, 1, 1), date(2024, 1, 10), date(2024, 1, 20), date(2024, 2, 1), date(2024, 2, 15)],
    'NS Checker Completion Date': [None, None, date(2024, 1, 25), None, date(2024, 2, 20)],
    'Docs Completion Date': [None, None, date(2024, 1, 22), None, date(2024, 2, 19)],
    'Maker Name': ['John', 'John', 'John', 'Alice', 'Alice'],
    'Checker Name': ['Mark', 'Mark', 'Mark', 'Bob', 'Bob'],
    'Sales Code': ['S123', 'S123', 'S123', 'S456', 'S456'],
}
df = pd.DataFrame(sample_data)

# Today's date
today = date.today()

# Ensure dates are clean
date_cols = ['Trigger Date', 'File Date', 'NS Checker Completion Date', 'Docs Completion Date']
for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors='coerce').dt.date

# Default missing trigger dates to file date
df['Trigger Date'] = df['Trigger Date'].fillna(df['File Date'])

# Sort for processing
df = df.sort_values(by=['AccountNumber', 'Review Type', 'File Date'])

# Function to calculate business days
def business_days_between(start_date, end_date):
    if pd.isna(start_date) or pd.isna(end_date):
        return 0
    return np.busday_count(start_date, end_date)

# Final results container
results = []

# Group by Account Number and Review Type
grouped = df.groupby(['AccountNumber', 'Review Type'])

for (account, review), group in grouped:
    group = group.sort_values(by='File Date')
    prev_doc = None
    prev_ns = None
    prev_date = None

    # Capture static fields like maker/checker/sales
    static_fields = group[['Maker Name', 'Checker Name', 'Sales Code']].dropna().iloc[0].to_dict()

    for i, row in group.iterrows():
        file_date = row['File Date']
        trigger_date = row['Trigger Date'] or file_date

        # --- Document Review Aging ---
        doc_status = row['Document Review Status']
        if pd.notna(doc_status):
            if doc_status != prev_doc:
                start_date = prev_date or trigger_date
                if 'completed' in str(doc_status).lower():
                    end_date = row['Docs Completion Date']
                else:
                    end_date = file_date or today
                if pd.isna(end_date):
                    end_date = today
                days = business_days_between(start_date, end_date)
                results.append({
                    'AccountNumber': account,
                    'Review Type': review,
                    'Process': 'Doc Review',
                    'Status': prev_doc,
                    'Days': days,
                    **static_fields
                })
                prev_doc = doc_status

        # --- Screening Aging ---
        ns_status = row['Screening Status']
        if pd.notna(ns_status):
            if ns_status != prev_ns:
                start_date = prev_date or trigger_date
                if 'completed' in str(ns_status).lower():
                    end_date = row['NS Checker Completion Date']
                else:
                    end_date = file_date or today
                if pd.isna(end_date):
                    end_date = today
                days = business_days_between(start_date, end_date)
                results.append({
                    'AccountNumber': account,
                    'Review Type': review,
                    'Process': 'Screening',
                    'Status': prev_ns,
                    'Days': days,
                    **static_fields
                })
                prev_ns = ns_status

        prev_date = file_date

# Create final DataFrame
result_df = pd.DataFrame(results)
result_df = result_df[result_df['Status'].notna()]  # remove initial nulls

# Preview
print(result_df.head())