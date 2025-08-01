import pandas as pd
from datetime import datetime

def calculate_status_ageing(df):
    # Ensure proper datetime types
    df['File Date'] = pd.to_datetime(df['File Date'])
    df['Trigger Date'] = pd.to_datetime(df['Trigger Date'])

    # Create unique Request ID
    df['Request ID'] = (
        df['Account ID'].astype(str) + '|' +
        df['Review Type'] + '|' +
        df['Trigger Date'].dt.strftime('%Y-%m-%d')
    )

    # Get all unique statuses
    doc_statuses = df['Doc Review Status'].dropna().unique()
    ns_statuses = df['Name Screening Status'].dropna().unique()

    doc_cols = [f'doc_{status}' for status in doc_statuses]
    ns_cols = [f'ns_{status}' for status in ns_statuses]

    df = df.sort_values(by=['Request ID', 'File Date']).reset_index(drop=True)
    today = pd.to_datetime(datetime.today().date())

    results = []

    for req_id, group in df.groupby('Request ID'):
        group = group.sort_values(by='File Date').reset_index(drop=True)

        # Static values
        trigger_date = group.loc[0, 'Trigger Date']
        ekyc_id = group.loc[0, 'eKYC ID']
        sales_code = group.loc[0, 'Sales Code']
        account_id = group.loc[0, 'Account ID']
        review_type = group.loc[0, 'Review Type']

        # Get all business days from trigger date to today (inclusive)
        full_bdays = pd.bdate_range(start=trigger_date, end=today)

        # Prepare a map of business day → status
        status_map = pd.DataFrame(index=full_bdays)
        status_map['Doc Status'] = None
        status_map['NS Status'] = None

        for i in range(len(group)):
            row = group.loc[i]
            file_date = row['File Date']
            if file_date in status_map.index:
                status_map.loc[file_date, 'Doc Status'] = row['Doc Review Status']
                status_map.loc[file_date, 'NS Status'] = row['Name Screening Status']

        # Fill missing days with last known status
        status_map['Doc Status'] = status_map['Doc Status'].ffill()
        status_map['NS Status'] = status_map['NS Status'].ffill()

        # Initialize ageing counters
        doc_age = {col: 0 for col in doc_cols}
        ns_age = {col: 0 for col in ns_cols}

        for _, row in status_map.iterrows():
            doc_col = f'doc_{row["Doc Status"]}'
            ns_col = f'ns_{row["NS Status"]}'
            if doc_col in doc_age:
                doc_age[doc_col] += 1
            if ns_col in ns_age:
                ns_age[ns_col] += 1

        total_ageing = len(status_map)  # Business days inclusive
        snapshot_count = len(group)     # How many days we captured

        latest_row = group.iloc[-1]

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
        result_row.update(doc_age)
        result_row.update(ns_age)
        results.append(result_row)

    result_df = pd.DataFrame(results)

    # Ensure all expected dynamic columns exist and are filled
    for col in doc_cols + ns_cols:
        if col not in result_df.columns:
            result_df[col] = 0

    result_df[doc_cols + ns_cols] = result_df[doc_cols + ns_cols].fillna(0).astype(int)

    return result_df