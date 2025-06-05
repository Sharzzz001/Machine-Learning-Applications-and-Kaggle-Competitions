import pandas as pd
import numpy as np
from datetime import datetime
import pyodbc
import time


def count_workdays(start_date, end_date):
    if pd.isnull(start_date) or pd.isnull(end_date):
        return np.nan
    return np.busday_count(start_date.date(), end_date.date())


def generate_current_status(aging_df):
    today = pd.to_datetime("today").normalize()

    aging_df['Date'] = pd.to_datetime(aging_df['Date'])
    aging_df['Focus List Entering Date'] = pd.to_datetime(aging_df['Focus List Entering Date'])
    aging_df['Latest Focus Week'] = pd.to_datetime(aging_df['Latest Focus Week'])

    aging_df['Days_Open'] = aging_df['Focus List Entering Date'].apply(
        lambda d: count_workdays(d, today) - 2
    )

    latest = (
        aging_df.sort_values('Date')
        .groupby('Account_No')
        .agg({
            'Date': 'last',
            'Status': 'last',
            'Status_screening': 'last',
            'Priority': 'last',
            'Focus List Entering Date': 'last',
            'Latest Focus Week': 'last',
            'Days_Open': 'last'
        })
        .reset_index()
    )

    one_month_ago = today - pd.DateOffset(months=1)

    skipped = latest[
        latest['Status'].isin([
            "Cancelled", "KYC Completed", "KYC Completed with Doc Deficiency",
            "On Hold", "Pending EAM/Introducer Agreement"
        ]) |
        ~latest['Priority'].isin(["Focus", "VIP"]) |
        (latest['Latest Focus Week'] < one_month_ago)
    ].copy()

    latest = latest[
        ~latest['Status'].isin([
            "Cancelled", "KYC Completed", "KYC Completed with Doc Deficiency",
            "On Hold", "Pending EAM/Introducer Agreement"
        ]) &
        (latest['Priority'].isin(["Focus", "VIP"])) &
        (latest['Latest Focus Week'] >= one_month_ago)
    ]

    return latest, skipped


def generate_doc_pivot(aging_df, doc_bin):
    doc_df = aging_df.merge(doc_bin, on="Status", how="left")
    doc_pivot = (
        doc_df.groupby("Account_No")["Doc_Status"]
        .value_counts().unstack(fill_value=0)
        .reset_index()
    )
    return doc_pivot


def generate_ns_pivot(aging_df, ns_bin):
    ns_df = aging_df.merge(ns_bin, on="Status_screening", how="left")
    ns_df["NS_Status"] = ns_df["NS_Status"].fillna("Not Updated")

    ns_pivot = (
        ns_df.groupby("Account_No")["NS_Status"]
        .value_counts().unstack(fill_value=0)
        .reset_index()
    )
    return ns_pivot


def load_data_from_access(db_path):
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        fr'DBQ={db_path};'
    )
    conn = pyodbc.connect(conn_str)

    aging_df = pd.read_sql("SELECT * FROM Aging_Table", conn)
    doc_bin = pd.read_sql("SELECT * FROM Bin_Table", conn)
    ns_bin = pd.read_sql("SELECT * FROM Bin_Table1", conn)

    conn.close()
    return aging_df, doc_bin, ns_bin


def generate_aging_report(db_path, output_file, skipped_output_file):
    start_time = time.time()

    aging_df, doc_bin, ns_bin = load_data_from_access(db_path)

    current_status, skipped_accounts = generate_current_status(aging_df)
    doc_pivot = generate_doc_pivot(aging_df, doc_bin)
    ns_pivot = generate_ns_pivot(aging_df, ns_bin)

    final_df = (
        current_status
        .merge(doc_pivot, on="Account_No", how="left")
        .merge(ns_pivot, on="Account_No", how="left")
    )

    final_df["Documentation"] = "Documentation"
    final_df["Name_Screening"] = "Name Screening"

    final_df = final_df.rename(columns={
        'Account_No': 'Account_ID',
        'Date': 'Date',
        'Days_Open': 'Total_Days_Aging',
        'Status': 'Latest_Doc_Status',
        'Status_screening': 'Latest_Name_Screening_Status',
        'Priority': 'Priority',
        'Focus List Entering Date': 'Date_Enter_Focus_List',
        'Latest Focus Week': 'Lastest_Focus_Week'
    })

    final_df.to_excel(output_file, index=False)
    skipped_accounts.to_excel(skipped_output_file, index=False)

    end_time = time.time()
    print(f"Execution time: {end_time - start_time:.2f} seconds")
    print(f"Skipped accounts exported to {skipped_output_file}")


if __name__ == "__main__":
    generate_aging_report(
        db_path="client_onboarding.accdb",
        output_file="Aging_Report.xlsx",
        skipped_output_file="Skipped_Accounts.xlsx"
    )
