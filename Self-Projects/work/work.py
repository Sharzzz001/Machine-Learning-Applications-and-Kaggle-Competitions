import pandas as pd
import numpy as np
from datetime import datetime

def calculate_status_ageing(df):
    # Convert to datetime
    df['File Date'] = pd.to_datetime(df['File Date'])
    df['Trigger Date'] = pd.to_datetime(df['Trigger Date'])

    # Unique request ID
    df['Request ID'] = df['Account ID'].astype(str) + '|' + df['Review Type'] + '|' + df['Trigger Date'].dt.strftime('%Y-%m-%d')

    # Get all unique statuses
    doc_statuses = df['Doc Review Status'].dropna().unique()
    ns_statuses = df['Name Screening Status'].dropna().unique()

    doc_cols = [f'doc_{status}' for status in doc_statuses]
    ns_cols = [f'ns_{status}' for status in ns_statuses]

    # Sort data
    df = df.sort_values(by=['Request ID', 'File Date']).reset_index(drop=True)

    # Today's date
    today = pd.to_datetime(datetime.today().date())

    results = []

    for req_id, group in df.groupby('Request ID'):
        group = group.sort_values(by='File Date').reset_index(drop=True)

        trigger_date = group.loc[0, 'Trigger Date']
        ekyc_id = group.loc[0, 'eKYC ID']
        sales_code = group.loc[0, 'Sales Code']
        account_id = group.loc[0, 'Account ID']
        review_type = group.loc[0, 'Review Type']

        # Create a business-day index from Trigger Date to Today
        full_bdays = pd.bdate_range(start=trigger_date, end=today)

        # Initialize a blank DataFrame to hold daily status values
        status_map = pd.DataFrame(index=full_bdays)
        status_map['Doc Status'] = None
        status_map['NS Status'] = None

        # Populate status on actual File Dates
        for i in range(len(group)):
            file_date = group.loc[i, 'File Date']
            doc_status = group.loc[i, 'Doc Review Status']
            ns_status = group.loc[i, 'Name Screening Status']
            if file_date in status_map.index:
                status_map.loc[file_date, 'Doc Status'] = doc_status
                status_map.loc[file_date, 'NS Status'] = ns_status

        # Forward fill missing statuses for business-day gaps
        status_map['Doc Status'] = status_map['Doc Status'].ffill()
        status_map['NS Status'] = status_map['NS Status'].ffill()

        # Initialize counters
        doc_age = {col: 0 for col in doc_cols}
        ns_age = {col: 0 for col in ns_cols}

        # Count ageing days for each status
        for _, row in status_map.iterrows():
            doc_col = f'doc_{row["Doc Status"]}'
            ns_col = f'ns_{row["NS Status"]}'
            if doc_col in doc_age:
                doc_age[doc_col] += 1
            if ns_col in ns_age:
                ns_age[ns_col] += 1

        # Prepare result row
        latest_row = group.iloc[-1]
        total_ageing = len(status_map)  # Only business days
        snapshot_count = len(group)     # How many days snapshots were captured

        result_row = {
            'Account ID': account_id,
            'Review Type': review_type,
            'Trigger Date': trigger_date,
            'eKYC ID': ekyc_id,
            'Sales Code': sales_code,
            'Total Ageing': total_ageing,
            'Snapshot Count': snapshot_count,
            'Latest Doc Status': latest_row['Doc Review Status'],
            'Latest Name Screening Status': latest_row['Name Screening Status'],
        }

        # Add ageing columns
        result_row.update(doc_age)
        result_row.update(ns_age)
        results.append(result_row)

    # Final result DataFrame
    result_df = pd.DataFrame(results)

    # Fill missing dynamic status columns with 0
    for col in doc_cols + ns_cols:
        if col not in result_df.columns:
            result_df[col] = 0

    result_df[doc_cols + ns_cols] = result_df[doc_cols + ns_cols].fillna(0).astype(int)

    return result_df