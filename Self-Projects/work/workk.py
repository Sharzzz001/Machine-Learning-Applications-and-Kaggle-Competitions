import pandas as pd
import numpy as np

# =====================================================
# CONFIGURATION
# =====================================================

INPUT_FILE  = r"daily_updates.xlsx"
OUTPUT_FILE = r"case_ageing_output.xlsx"

CASE_COL   = "Case Number"
STATUS_COL = "Pending with Status"
DATE_COL   = "Business Date"

# =====================================================
# LOAD DATA
# =====================================================

df = pd.read_excel(INPUT_FILE)

df[DATE_COL] = pd.to_datetime(df[DATE_COL])
df = df.sort_values([CASE_COL, DATE_COL])

# =====================================================
# IDENTIFY STATUS CHANGE POINTS
# =====================================================

df["Prev_Status"] = df.groupby(CASE_COL)[STATUS_COL].shift(1)

df["Status_Change"] = df[STATUS_COL] != df["Prev_Status"]
df.loc[df["Prev_Status"].isna(), "Status_Change"] = True

# =====================================================
# BUILD STATUS INTERVALS
# =====================================================

intervals = (
    df[df["Status_Change"]]
    .assign(
        Start_Date=lambda x: x[DATE_COL],
        End_Date=lambda x: x.groupby(CASE_COL)[DATE_COL].shift(-1)
    )
)

# Last interval ends on last available business date
last_seen_date = df.groupby(CASE_COL)[DATE_COL].max()

intervals["End_Date"] = intervals["End_Date"].fillna(
    intervals[CASE_COL].map(last_seen_date)
)

# =====================================================
# BUSINESS DAY AGEING FUNCTION
# =====================================================

def business_days(start, end):
    """
    Business days between two dates (end exclusive).
    """
    return np.busday_count(start.date(), end.date())


intervals["Ageing"] = intervals.apply(
    lambda r: business_days(r["Start_Date"], r["End_Date"]),
    axis=1
)

# =====================================================
# STATUS-WISE AGEING (PIVOT)
# =====================================================

status_ageing = (
    intervals
    .groupby([CASE_COL, STATUS_COL])["Ageing"]
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)

status_cols = [c for c in status_ageing.columns if c != CASE_COL]

status_ageing["Total_Ageing"] = status_ageing[status_cols].sum(axis=1)

# =====================================================
# LATEST STATUS
# =====================================================

latest_status = (
    df
    .sort_values([CASE_COL, DATE_COL])
    .groupby(CASE_COL)
    .tail(1)
    [[CASE_COL, STATUS_COL, DATE_COL]]
    .rename(columns={
        STATUS_COL: "Latest_Status",
        DATE_COL: "Latest_Date"
    })
)

# =====================================================
# LATEST STATUS AGEING (CONTINUOUS RUN)
# =====================================================

def latest_status_ageing(case_df):
    case_df = case_df.sort_values(DATE_COL)

    latest_status = case_df[STATUS_COL].iloc[-1]
    latest_date = case_df[DATE_COL].iloc[-1]

    reversed_df = case_df.iloc[::-1]

    start_date = latest_date

    for _, row in reversed_df.iterrows():
        if row[STATUS_COL] == latest_status:
            start_date = row[DATE_COL]
        else:
            break

    return np.busday_count(start_date.date(), latest_date.date())


latest_status_ageing_df = (
    df
    .groupby(CASE_COL)
    .apply(latest_status_ageing)
    .reset_index(name="Latest_Status_Ageing")
)

# =====================================================
# STATIC COLUMNS (LATEST SNAPSHOT)
# =====================================================

static_cols = (
    df
    .sort_values([CASE_COL, DATE_COL])
    .drop_duplicates(subset=[CASE_COL], keep="last")
    .drop(columns=[DATE_COL, "Prev_Status", "Status_Change"])
)

# =====================================================
# FINAL DATASET
# =====================================================

final_df = (
    static_cols
    .merge(status_ageing, on=CASE_COL, how="left")
    .merge(latest_status[[CASE_COL, "Latest_Status"]], on=CASE_COL, how="left")
    .merge(latest_status_ageing_df, on=CASE_COL, how="left")
)

# =====================================================
# OUTPUT
# =====================================================

final_df.to_excel(OUTPUT_FILE, index=False)

print("========================================")
print("Case ageing file generated successfully")
print(f"Output: {OUTPUT_FILE}")
print("========================================")