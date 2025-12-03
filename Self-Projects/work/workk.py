import pandas as pd

CASE_COL = "case_report"
STATUS_COL = "Pending with Status"
FILE_DATE_COL = "File Date"

df_snapshots = simulated_df  # from your previous step

# 1. Status counts per case (wide)
status_counts = (
    df_snapshots
    .groupby([CASE_COL, STATUS_COL])
    .size()
    .unstack(fill_value=0)      # statuses become columns with counts
    .reset_index()
)

# 2. Add Total_Ageing as sum of all status columns
status_cols = [c for c in status_counts.columns if c != CASE_COL]
status_counts["Total_Ageing"] = status_counts[status_cols].sum(axis=1)


# 3. Base static row per case (latest snapshot, no File Date)
#    This also gives us the Latest Status for each case
base_df = (
    df_snapshots
    .sort_values([CASE_COL, FILE_DATE_COL])     # oldest → newest
    .drop_duplicates(subset=[CASE_COL], keep="last")
    .drop(columns=[FILE_DATE_COL])             # File Date not needed in final df
)

# base_df now has CASE_COL, STATUS_COL (latest status), and all other static cols


# 4. Merge static info + status counts
final_df = base_df.merge(status_counts, on=CASE_COL, how="left")

# 5. Compute Latest_Status_Ageing:
#    for each row, pick the count from the column matching its latest status
def compute_latest_status_ageing(row):
    latest_status = row[STATUS_COL]
    # If that status exists as a column, return its count, else 0 (safety net)
    if pd.isna(latest_status):
        return 0
    return row.get(latest_status, 0)

final_df["Latest_Status_Ageing"] = final_df.apply(compute_latest_status_ageing, axis=1)

print(final_df.head())