import pandas as pd
import pyodbc

# --- CONFIG ---
ACCESS_DB_PATH = r"C:\path\to\RR_Request_DB.accdb"
TABLE_NAME = "Snapshots"
STATUS_COLUMNS = ["Screenings", "Documents Ready for Review"]

# --- Read from Access ---
def read_snapshots_from_access(db_path, table_name):
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        rf"DBQ={db_path};"
    )
    conn = pyodbc.connect(conn_str)
    df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
    conn.close()
    return df

# --- Aging Logic ---
def calculate_status_aging(df, status_col):
    df = df.copy()
    df["file_date"] = pd.to_datetime(df["file_date"])
    df["Trigger Date"] = pd.to_datetime(df["Trigger Date"], errors="coerce")
    df = df.dropna(subset=["Trigger Date", status_col])

    df = df.sort_values(by=["Title", "Review Type", "Trigger Date", "file_date"])

    results = []

    group_cols = ["Title", "Review Type", "Trigger Date"]
    for group_keys, group in df.groupby(group_cols):
        title, review_type, trigger_date = group_keys
        group = group[["file_date", status_col]].dropna()

        prev_status = None
        prev_start_date = trigger_date  # Start from Trigger Date

        for i, row in group.iterrows():
            curr_status = row[status_col]
            curr_file_date = row["file_date"]

            if pd.isna(curr_status):
                continue

            if prev_status is None:
                prev_status = curr_status
                prev_start_date = trigger_date  # First snapshot → use Trigger Date
            elif curr_status != prev_status:
                # Status changed → close the previous one
                results.append({
                    "Title": title,
                    "Review Type": review_type,
                    "Trigger Date": trigger_date.date(),
                    "Status Type": status_col,
                    "Status Value": prev_status,
                    "Start Date": prev_start_date.date(),
                    "End Date": curr_file_date.date(),
                    "Duration (days)": (curr_file_date - prev_start_date).days
                })
                # Start new status aging
                prev_status = curr_status
                prev_start_date = curr_file_date

        # Handle last open status (up to latest snapshot date)
        if prev_status is not None:
            last_file_date = group["file_date"].max()
            results.append({
                "Title": title,
                "Review Type": review_type,
                "Trigger Date": trigger_date.date(),
                "Status Type": status_col,
                "Status Value": prev_status,
                "Start Date": prev_start_date.date(),
                "End Date": last_file_date.date(),
                "Duration (days)": (last_file_date - prev_start_date).days + 1
            })

    return pd.DataFrame(results)

# --- Run full aging ---
def calculate_aging_from_access(db_path, table_name, status_columns):
    df = read_snapshots_from_access(db_path, table_name)

    aging_frames = []
    for status_col in status_columns:
        aging_df = calculate_status_aging(df, status_col)
        aging_frames.append(aging_df)

    return pd.concat(aging_frames, ignore_index=True)

# --- Execute ---
aging_df = calculate_aging_from_access(ACCESS_DB_PATH, TABLE_NAME, STATUS_COLUMNS)

# Show or save
print(aging_df.head())
aging_df.to_excel("accurate_status_aging.xlsx", index=False)




import pandas as pd

# Load both snapshot files
file1 = pd.read_excel("RR_Request_2025-07-02.xlsx")
file2 = pd.read_excel("RR_Request_2025-07-03.xlsx")

# Columns to compare
key_cols = ["Title", "Review Type"]
status_cols = ["Screenings", "Documents Ready for Review"]

# Merge on Title + Review Type
merged = file1[key_cols + status_cols].merge(
    file2[key_cols + status_cols],
    on=key_cols,
    suffixes=("_old", "_new"),
    how="inner"
)

# Identify changes
for col in status_cols:
    merged[f"{col}_changed"] = merged[f"{col}_old"] != merged[f"{col}_new"]

# Filter rows where any status changed
changed = merged[merged[[f"{col}_changed" for col in status_cols]].any(axis=1)]

# Show changes
print(changed[[*key_cols, *status_cols, *(f"{col}_changed" for col in status_cols)]])