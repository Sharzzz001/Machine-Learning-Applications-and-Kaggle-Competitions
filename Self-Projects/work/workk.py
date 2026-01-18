import pandas as pd
import numpy as np

# ======================================================
# CONFIG
# ======================================================

INPUT_FILE  = r"daily_updates.xlsx"
OUTPUT_FILE = r"case_ageing_output.xlsx"

CASE_COL   = "Case Number"
STATUS_COL = "Pending with Status"
DATE_COL   = "Business Date"

# ======================================================
# LOAD DATA
# ======================================================

df = pd.read_excel(INPUT_FILE)

df[DATE_COL] = pd.to_datetime(df[DATE_COL])
df = df.sort_values([CASE_COL, DATE_COL])

# ======================================================
# CALCULATE NEXT SNAPSHOT DATE
# ======================================================

df["Next_Date"] = df.groupby(CASE_COL)[DATE_COL].shift(-1)

# ======================================================
# BUSINESS DAY AGEING BETWEEN SNAPSHOTS
# ======================================================

def business_day_diff(d1, d2):
    """
    Counts business days between two snapshot dates.
    End date excluded.
    """
    if pd.isna(d2):
        return 1
    return np.busday_count(d1.date(), d2.date())

df["Row_Ageing"] = df.apply(
    lambda r: business_day_diff(r[DATE_COL], r["Next_Date"]),
    axis=1
)

# ======================================================
# STATUS-WISE AGEING
# ======================================================

status_ageing = (
    df
    .groupby([CASE_COL, STATUS_COL])["Row_Ageing"]
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)

status_cols = [c for c in status_ageing.columns if c != CASE_COL]
status_ageing["Total_Ageing"] = status_ageing[status_cols].sum(axis=1)

# ======================================================
# LATEST STATUS
# ======================================================

latest_status = (
    df
    .sort_values([CASE_COL, DATE_COL])
    .groupby(CASE_COL)
    .tail(1)
    [[CASE_COL, STATUS_COL]]
    .rename(columns={STATUS_COL: "Latest_Status"})
)

# ======================================================
# LATEST STATUS AGEING
# ======================================================

latest_status_ageing = (
    df
    .sort_values([CASE_COL, DATE_COL])
    .groupby(CASE_COL)
    .tail(1)
    [[CASE_COL, "Row_Ageing"]]
    .rename(columns={"Row_Ageing": "Latest_Status_Ageing"})
)

# ======================================================
# STATIC COLUMNS (LATEST SNAPSHOT)
# ======================================================

static_cols = (
    df
    .sort_values([CASE_COL, DATE_COL])
    .drop_duplicates(subset=[CASE_COL], keep="last")
    .drop(columns=["Next_Date", "Row_Ageing"])
)

# ======================================================
# FINAL DATASET
# ======================================================

final_df = (
    static_cols
    .merge(status_ageing, on=CASE_COL, how="left")
    .merge(latest_status, on=CASE_COL, how="left")
    .merge(latest_status_ageing, on=CASE_COL, how="left")
)

# ======================================================
# OUTPUT
# ======================================================

final_df.to_excel(OUTPUT_FILE, index=False)

print("========================================")
print("Ageing calculation completed successfully")
print(f"Output file: {OUTPUT_FILE}")
print("========================================")