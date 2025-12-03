CASE_COL = "case_report"
STATUS_COL = "Pending with Status"
FILE_DATE_COL = "File Date"

df_snapshots = simulated_df  # from previous step

# Count how many times each status appears per case
status_counts = (
    df_snapshots
    .groupby([CASE_COL, STATUS_COL])
    .size()
    .unstack(fill_value=0)      # make statuses into columns
    .reset_index()
)

# Optional: rename columns to be nicer (e.g., prefix with 'status_')
# status_counts = status_counts.rename(columns=lambda c: f"status_{c}" if c != CASE_COL else c)

# Sort so latest date per case is last
base_df = (
    df_snapshots
    .sort_values([CASE_COL, FILE_DATE_COL])
    .drop_duplicates(subset=[CASE_COL], keep="last")
    .drop(columns=[FILE_DATE_COL])   # remove File Date from final
)

final_df = base_df.merge(status_counts, on=CASE_COL, how="left")

