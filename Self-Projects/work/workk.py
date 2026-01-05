CASE_COL        = "Name"
LIFECYCLE_COL   = "Status"                  # In progress / Completed
SUB_STATUS_COL  = "Pending with Status"     # only for In progress
DATE_COL        = "File Date"

IN_PROGRESS_VAL = "In progress"
COMPLETED_VAL   = "Completed"

df = df_snapshots.copy()
df[DATE_COL] = pd.to_datetime(df[DATE_COL])
df = df.sort_values([CASE_COL, DATE_COL])

latest_lifecycle = (
    df
    .sort_values([CASE_COL, DATE_COL])
    .groupby(CASE_COL)
    .tail(1)
    [[CASE_COL, LIFECYCLE_COL]]
)

active_cases = latest_lifecycle[
    latest_lifecycle[LIFECYCLE_COL] == IN_PROGRESS_VAL
][CASE_COL]

df_ip = df[
    (df[LIFECYCLE_COL] == IN_PROGRESS_VAL) &
    (df[CASE_COL].isin(active_cases))
].copy()


df_ip["Prev_Status"] = df_ip.groupby(CASE_COL)[SUB_STATUS_COL].shift(1)
df_ip["Status_Change"] = df_ip[SUB_STATUS_COL] != df_ip["Prev_Status"]
df_ip.loc[df_ip["Prev_Status"].isna(), "Status_Change"] = True



intervals = (
    df_ip[df_ip["Status_Change"]]
    .assign(
        Start_Date=lambda x: x[DATE_COL],
        End_Date=lambda x: x.groupby(CASE_COL)[DATE_COL].shift(-1)
    )
)

latest_ip_date = df_ip.groupby(CASE_COL)[DATE_COL].max()
intervals["End_Date"] = intervals["End_Date"].fillna(
    intervals[CASE_COL].map(latest_ip_date)
)


import numpy as np

def business_days(start, end):
    return np.busday_count(start.date(), end.date())

intervals["Ageing"] = intervals.apply(
    lambda r: business_days(r["Start_Date"], r["End_Date"]),
    axis=1
)



status_ageing = (
    intervals
    .groupby([CASE_COL, SUB_STATUS_COL])["Ageing"]
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)

status_cols = [c for c in status_ageing.columns if c != CASE_COL]
status_ageing["Total_Ageing"] = status_ageing[status_cols].sum(axis=1)


latest_ip_snapshot = (
    df_ip
    .sort_values([CASE_COL, DATE_COL])
    .groupby(CASE_COL)
    .tail(1)
    [[CASE_COL, SUB_STATUS_COL, DATE_COL]]
    .rename(columns={
        SUB_STATUS_COL: "Latest_Status",
        DATE_COL: "Latest_File_Date"
    })
)

def latest_status_ageing(case_df):
    case_df = case_df.sort_values(DATE_COL)
    latest_status = case_df[SUB_STATUS_COL].iloc[-1]
    latest_date = case_df[DATE_COL].iloc[-1]

    reversed_df = case_df.iloc[::-1]

    start_date = latest_date
    for _, row in reversed_df.iterrows():
        if row[SUB_STATUS_COL] == latest_status:
            start_date = row[DATE_COL]
        else:
            break

    return np.busday_count(start_date.date(), latest_date.date())
    
    
latest_status_ageing_df = (
    df_ip
    .groupby(CASE_COL)
    .apply(latest_status_ageing)
    .reset_index(name="Latest_Status_Ageing")
)

static_cols_df = (
    df
    .sort_values([CASE_COL, DATE_COL])
    .drop_duplicates(subset=[CASE_COL], keep="last")
)

static_cols_df = static_cols_df[
    static_cols_df[CASE_COL].isin(active_cases)
].drop(columns=[DATE_COL])


final_df = (
    static_cols_df
    .merge(status_ageing, on=CASE_COL, how="left")
    .merge(latest_ip_snapshot[[CASE_COL, "Latest_Status"]], on=CASE_COL, how="left")
    .merge(latest_status_ageing_df, on=CASE_COL, how="left")
)


