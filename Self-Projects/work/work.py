import pandas as pd
from datetime import datetime

def calculate_status_ageing(df):
    # Convert dates
    df['File_Date'] = pd.to_datetime(df['File_Date'])
    df['Trigger_Date'] = pd.to_datetime(df['Trigger_Date'])

    # Create unique request ID
    df['Request_ID'] = (
        df['Account_ID'].astype(str) + '|' +
        df['Review_Type'].astype(str) + '|' +
        df['Trigger_Date'].dt.strftime('%Y-%m-%d')
    )

    # Unique status values
    doc_statuses = df['Doc_Status'].dropna().unique()
    ns_statuses = df['Screening_Status'].dropna().unique()

    doc_cols = [f'doc_{status}' for status in doc_statuses]
    ns_cols = [f'ns_{status}' for status in ns_statuses]

    # Sort and initialize
    df = df.sort_values(by=['Request_ID', 'File_Date']).reset_index(drop=True)
    today = pd.to_datetime(datetime.today().date())
    results = []

    for req_id, group in df.groupby('Request_ID'):
        group = group.sort_values(by='File_Date').reset_index(drop=True)

        # Common fields
        trigger_date = group.loc[0, 'Trigger_Date']
        account_id = group.loc[0, 'Account_ID']
        review_type = group.loc[0, 'Review_Type']
        ekycid = group.loc[0, 'ekycID']

        # Business days between Trigger → Today (inclusive)
        full_bdays = pd.bdate_range(start=trigger_date, end=today)

        # Status map
        status_map = pd.DataFrame(index=full_bdays)
        status_map['Doc_Status'] = None
        status_map['Screening_Status'] = None

        for i in range(len(group)):
            file_date = group.loc[i, 'File_Date']
            doc_status = group.loc[i, 'Doc_Status']
            screening_status = group.loc[i, 'Screening_Status']
            if file_date in status_map.index:
                status_map.loc[file_date, 'Doc_Status'] = doc_status
                status_map.loc[file_date, 'Screening_Status'] = screening_status

        # Fill gaps with forward fill
        status_map['Doc_Status'] = status_map['Doc_Status'].ffill()
        status_map['Screening_Status'] = status_map['Screening_Status'].ffill()

        # Initialize ageing counters
        doc_age = {col: 0 for col in doc_cols}
        ns_age = {col: 0 for col in ns_cols}

        for _, row in status_map.iterrows():
            doc_col = f'doc_{row["Doc_Status"]}'
            ns_col = f'ns_{row["Screening_Status"]}'
            if doc_col in doc_age:
                doc_age[doc_col] += 1
            if ns_col in ns_age:
                ns_age[ns_col] += 1

        # Get latest statuses
        latest_doc_status = status_map['Doc_Status'].iloc[-1]
        latest_ns_status = status_map['Screening_Status'].iloc[-1]

        # Count ageing for current (latest) status
        doc_status_age = (status_map['Doc_Status'][::-1] == latest_doc_status).cumsum().where(lambda x: x == 1).count()
        ns_status_age = (status_map['Screening_Status'][::-1] == latest_ns_status).cumsum().where(lambda x: x == 1).count()

        result_row = {
            'Account_ID': account_id,
            'Review_Type': review_type,
            'Trigger_Date': trigger_date,
            'ekycID': ekycid,
            'Total_Ageing': len(status_map),
            'Snapshot_Count': len(group),
            'Latest_Doc_Status': latest_doc_status,
            'Latest_Doc_Status_Ageing': doc_status_age,
            'Latest_Screening_Status': latest_ns_status,
            'Latest_Screening_Status_Ageing': ns_status_age
        }

        # Add dynamic status ageing columns
        result_row.update(doc_age)
        result_row.update(ns_age)
        results.append(result_row)

    # Build final dataframe
    result_df = pd.DataFrame(results)

    # Ensure all dynamic columns exist and are filled
    for col in doc_cols + ns_cols:
        if col not in result_df.columns:
            result_df[col] = 0

    result_df[doc_cols + ns_cols] = result_df[doc_cols + ns_cols].fillna(0).astype(int)

    return result_df