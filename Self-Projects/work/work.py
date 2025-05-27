import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- Helper function to mimic VBA's CountWorkDays
def count_workdays_vba(start_date, end_date):
    if pd.isna(start_date) or pd.isna(end_date):
        return np.nan

    # Align to Monday
    start = start_date - timedelta(days=start_date.weekday())
    end = end_date - timedelta(days=end_date.weekday())

    workdays = ((end - start).days // 7) * 5 + 1
    temp = start_date
    while temp < end_date:
        if temp.weekday() < 5:
            workdays += 1
        temp += timedelta(days=1)

    return workdays

# --- Function to replicate Documentation pivot
def create_documentation_pivot(aging_df, bin_df):
    merged = aging_df.merge(bin_df, how='left', on='Status')
    doc_pivot = pd.crosstab(merged['Account_No'], merged['Doc_Status']).reset_index()
    return doc_pivot

# --- Function to replicate Name Screening pivot
def create_name_screening_pivot(aging_df, bin1_df):
    merged = aging_df.merge(bin1_df, how='left', on='Status_screening')
    merged['NS_Status'] = merged['NS_Status'].fillna("Not Updated")
    ns_pivot = pd.crosstab(merged['Account_No'], merged['NS_Status']).reset_index()
    return ns_pivot

# --- Function to replicate Current_Status query
def create_current_status(aging_df):
    aging_df['Date'] = pd.to_datetime(aging_df['Date'], errors='coerce')
    aging_df['Focus List Entering Date'] = pd.to_datetime(aging_df['Focus List Entering Date'], errors='coerce')
    aging_df['Latest Focus Week'] = pd.to_datetime(aging_df['Latest Focus Week'], errors='coerce')

    today = pd.to_datetime("today")

    # Compute Days_Open
    aging_df['Days_Open'] = aging_df['Focus List Entering Date'].apply(
        lambda d: np.nan if pd.isna(d) else count_workdays_vba(d, today) - 2
    )

    # Sort so 'last' row per account is the latest
    sorted_df = aging_df.sort_values('Date')
    last_df = sorted_df.groupby('Account_No').last().reset_index()

    # Rename columns
    last_df = last_df.rename(columns={
        'Date': 'LastOfDate',
        'Status': 'LastOfStatus',
        'Status_screening': 'LastOfStatus_screening',
        'Priority': 'LastOfPriority',
        'Focus List Entering Date': 'LastOfFocus List Entering Date',
        'Latest Focus Week': 'LastOfLatest Focus Week',
        'Days_Open': 'Days_Open'
    })

    return last_df

# --- Final Aging Table
def create_final_aging_table(aging_df, bin_df, bin1_df):
    current_status = create_current_status(aging_df)

    # Filter per Access logic
    excluded_statuses = [
        "Cancelled", "KYC Completed", "KYC Completed with Doc Deficiency",
        "On Hold", "Pending EAM/Introducer Agreement"
    ]
    current_status_filtered = current_status[
        (~current_status['LastOfStatus'].isin(excluded_statuses)) &
        (current_status['LastOfPriority'].isin(["Focus", "VIP"])) &
        (current_status['LastOfLatest Focus Week'] >= pd.to_datetime("today") - pd.DateOffset(months=1))
    ]

    doc_pivot = create_documentation_pivot(aging_df, bin_df)
    ns_pivot = create_name_screening_pivot(aging_df, bin1_df)

    # Merge everything
    final = current_status_filtered.merge(doc_pivot, how='left', on='Account_No')
    final = final.merge(ns_pivot, how='left', on='Account_No')

    # Fill NaNs with 0 for pivot columns (optional)
    pivot_cols = list(set(final.columns) - set(current_status_filtered.columns))
    final[pivot_cols] = final[pivot_cols].fillna(0).astype(int)

    return final