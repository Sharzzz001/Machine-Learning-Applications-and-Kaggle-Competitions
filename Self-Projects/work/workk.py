CASE_COL = "case_report"
STATUS_COL = "Pending with Status"
FILE_DATE_COL = "File Date"

df_snapshots = simulated_df  # from earlier step


# 1. Status counts per case (wide)
status_counts = (
    df_snapshots
    .groupby([CASE_COL, STATUS_COL])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

# 2. Add Total_Ageing as sum of all status columns
status_cols = [c for c in status_counts.columns if c != CASE_COL]
status_counts["Total_Ageing"] = status_counts[status_cols].sum(axis=1)


# 3. Base static row per case (latest snapshot, no File Date)
base_df = (
    df_snapshots
    .sort_values([CASE_COL, FILE_DATE_COL])     # oldest → newest
    .drop_duplicates(subset=[CASE_COL], keep="last")
    .drop(columns=[FILE_DATE_COL])             # File Date not needed in final df
)

# 4. Merge static info + status counts + total ageing
final_df = base_df.merge(status_counts, on=CASE_COL, how="left")

print(final_df.head())