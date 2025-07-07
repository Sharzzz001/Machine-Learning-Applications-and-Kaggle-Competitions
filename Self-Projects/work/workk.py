COMPARE_DATE_1 = "2025-07-02"
COMPARE_DATE_2 = "2025-07-03"

import pandas as pd
import pyodbc

# --- CONFIG: EDIT THESE ---
ACCESS_DB_PATH = r"C:\path\to\RR_Request_DB.accdb"
TABLE_NAME = "Snapshots"

COMPARE_DATE_1 = "2025-07-02"  # First snapshot date
COMPARE_DATE_2 = "2025-07-03"  # Second snapshot date
TRIGGER_DATE_THRESHOLD = "2025-07-02"

# --- Load data from Access ---
def load_data(date1, date2):
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        rf"DBQ={ACCESS_DB_PATH};"
    )
    conn = pyodbc.connect(conn_str)
    
    query = f"""
        SELECT [Title], [Review Type], [Trigger Date],
               [Screenings], [Documents Ready for Review], [file_date]
        FROM [{TABLE_NAME}]
        WHERE [Trigger Date] > #{TRIGGER_DATE_THRESHOLD}#
          AND file_date IN (#{date1}#, #{date2}#)
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- Compare snapshots ---
def compare_snapshots(df, date1, date2):
    df["file_date"] = pd.to_datetime(df["file_date"])
    df["Trigger Date"] = pd.to_datetime(df["Trigger Date"])
    df["file_date_str"] = df["file_date"].dt.strftime("%Y-%m-%d")

    # Pivot screenings
    screening_pivot = df.pivot_table(
        index=["Title", "Review Type", "Trigger Date"],
        columns="file_date_str",
        values="Screenings",
        aggfunc="first"
    ).rename(columns={
        date1: f"Screening {date1}",
        date2: f"Screening {date2}"
    })

    # Pivot document status
    document_pivot = df.pivot_table(
        index=["Title", "Review Type", "Trigger Date"],
        columns="file_date_str",
        values="Documents Ready for Review",
        aggfunc="first"
    ).rename(columns={
        date1: f"Document {date1}",
        date2: f"Document {date2}"
    })

    # Merge
    merged = screening_pivot.join(document_pivot, how="outer").reset_index()

    # Add change flags
    merged["Screening Changed"] = merged[f"Screening {date1}"] != merged[f"Screening {date2}"]
    merged["Document Changed"] = merged[f"Document {date1}"] != merged[f"Document {date2}"]

    return merged

# --- Run Script ---
df = load_data(COMPARE_DATE_1, COMPARE_DATE_2)
comparison_df = compare_snapshots(df, COMPARE_DATE_1, COMPARE_DATE_2)

# Display or save
print(comparison_df.head())
comparison_df.to_excel(f"status_change_{COMPARE_DATE_1}_to_{COMPARE_DATE_2}.xlsx", index=False)