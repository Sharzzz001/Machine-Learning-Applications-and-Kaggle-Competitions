import pandas as pd
import pyodbc

# --- CONFIGURATION ---
ACCESS_DB_PATH = r"C:\path\to\RR_Request_DB.accdb"
TABLE_NAME = "Snapshots"
STATUS_COLUMNS = ["Screenings", "Documents Ready for Review"]

# --- Connect to Access DB ---
def read_snapshots_from_access(db_path, table_name):
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        rf"DBQ={db_path};"
    )
    conn = pyodbc.connect(conn_str)
    df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
    conn.close()
    return df

# --- Calculate aging for one status column ---
def calculate_status_aging(df, status_col):
    df = df.copy()
    df["file_date"] = pd.to_datetime(df["file_date"])
    df = df.sort_values(by=["Title", "Review Type", "file_date"])

    results = []

    for (title, review_type), group in df.groupby(["Title", "Review Type"]):
        group = group[["file_date", status_col]].dropna().sort_values("file_date")
        if group.empty:
            continue

        prev_status = None
        start_date = None

        for i, row in group.iterrows():
            curr_status = row[status_col]
            curr_date = row["file_date"]

            if pd.isna(curr_status):
                continue

            if prev_status is None:
                # First valid status
                prev_status = curr_status
                start_date = curr_date
            elif curr_status != prev_status:
                # Status changed → close previous status period
                results.append({
                    "Title": title,
                    "Review Type": review_type,
                    "Status Type": status_col,
                    "Status Value": prev_status,
                    "Start Date": start_date,
                    "End Date": curr_date,
                    "Duration (days)": (curr_date - start_date).days
                })
                # Start new period
                prev_status = curr_status
                start_date = curr_date

        # Add last open period till last date
        if prev_status is not None and start_date is not None:
            end_date = group["file_date"].max()
            duration = (end_date - start_date).days + 1  # Include final day
            results.append({
                "Title": title,
                "Review Type": review_type,
                "Status Type": status_col,
                "Status Value": prev_status,
                "Start Date": start_date,
                "End Date": end_date,
                "Duration (days)": duration
            })

    return pd.DataFrame(results)

# --- Main aging calculator ---
def calculate_aging_from_access(db_path, table_name, status_columns):
    df = read_snapshots_from_access(db_path, table_name)

    aging_frames = []
    for status_col in status_columns:
        aging_df = calculate_status_aging(df, status_col)
        aging_frames.append(aging_df)

    return pd.concat(aging_frames, ignore_index=True)

# --- RUN ---
aging_df = calculate_aging_from_access(ACCESS_DB_PATH, TABLE_NAME, STATUS_COLUMNS)

# Show result
print(aging_df.head())

# Optional: Save to Excel
aging_df.to_excel("status_aging_output.xlsx", index=False)