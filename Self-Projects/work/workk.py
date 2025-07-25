import pandas as pd
import numpy as np
from datetime import datetime

def calculate_status_ageing(df):
    # Ensure proper dtypes
    df['File Date'] = pd.to_datetime(df['File Date'])
    df['Trigger Date'] = pd.to_datetime(df['Trigger Date'])
    
    # Create unique request ID
    df['Request ID'] = df['Account ID'].astype(str) + '|' + df['Review Type'] + '|' + df['Trigger Date'].dt.strftime('%Y-%m-%d')
    
    # Get all unique statuses
    doc_statuses = df['Doc Review Status'].dropna().unique()
    ns_statuses = df['Name Screening Status'].dropna().unique()

    doc_cols = [f'doc_{status}' for status in doc_statuses]
    ns_cols = [f'ns_{status}' for status in ns_statuses]

    # Sort by Request and File Date
    df = df.sort_values(by=['Request ID', 'File Date']).reset_index(drop=True)

    # Output list
    results = []

    # Today's date for open cases
    today = pd.to_datetime(datetime.today().date())

    for req_id, group in df.groupby('Request ID'):
        group = group.sort_values(by='File Date').reset_index(drop=True)
        trigger_date = group.loc[0, 'Trigger Date']
        ekyc_id = group.loc[0, 'eKYC ID']
        sales_code = group.loc[0, 'Sales Code']
        account_id = group.loc[0, 'Account ID']
        review_type = group.loc[0, 'Review Type']

        # Initialize ageing trackers with 0
        doc_age = {col: 0 for col in doc_cols}
        ns_age = {col: 0 for col in ns_cols}

        # Status processing
        for i in range(len(group)):
            row = group.loc[i]
            curr_date = row['File Date']

            # Determine ageing range
            if i == 0:
                start_date = trigger_date
            else:
                start_date = group.loc[i-1, 'File Date']

            if i < len(group) - 1:
                end_date = group.loc[i+1, 'File Date']
            else:
                end_date = today

            # Calculate business days
            days = np.busday_count(start_date.date(), end_date.date())

            # Assign to doc and ns status columns
            doc_col = f'doc_{row["Doc Review Status"]}'
            ns_col = f'ns_{row["Name Screening Status"]}'
            if doc_col in doc_age:
                doc_age[doc_col] += days
            if ns_col in ns_age:
                ns_age[ns_col] += days

        total_ageing = np.busday_count(trigger_date.date(), today.date())
        latest_row = group.iloc[-1]
        
        # Build result row
        result_row = {
            'Account ID': account_id,
            'Review Type': review_type,
            'Trigger Date': trigger_date,
            'eKYC ID': ekyc_id,
            'Sales Code': sales_code,
            'Total Ageing': total_ageing,
            'Latest Doc Status': latest_row['Doc Review Status'],
            'Latest Name Screening Status': latest_row['Name Screening Status'],
        }
        result_row.update(doc_age)
        result_row.update(ns_age)
        results.append(result_row)

    # Final result DataFrame
    result_df = pd.DataFrame(results)

    # Fill any missing dynamic columns with 0
    for col in doc_cols + ns_cols:
        if col not in result_df.columns:
            result_df[col] = 0

    # Replace any accidental NaNs with 0s
    result_df[doc_cols + ns_cols] = result_df[doc_cols + ns_cols].fillna(0).astype(int)
    
    return result_df