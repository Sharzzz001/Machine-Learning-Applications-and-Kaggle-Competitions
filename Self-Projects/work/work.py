"""
replicate_aging_queries.py
-------------------------
Everything below assumes you already have three pandas DataFrames in memory:

    aging_df  : the whole Aging_Table
    bin_df    : two columns  [Status,        Doc_Status]
    bin1_df   : two columns  [Status_screening, NS_Status]

Nothing is read from or written to disk here.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ------------------------------------------------------------------ #
# 1. helper – VBA‑compatible CountWorkDays()                         #
# ------------------------------------------------------------------ #
def count_workdays_vba(start_date: pd.Timestamp,
                       end_date: pd.Timestamp | None = None) -> int | float:
    """Mimic the Access/VBA CountWorkDays used in Current_Status."""
    if pd.isna(start_date):
        return np.nan
    if end_date is None:
        end_date = pd.Timestamp("today").normalize()

    # Align both to the Monday of their weeks
    start_aligned = start_date - timedelta(days=start_date.weekday())
    end_aligned   = end_date   - timedelta(days=end_date.weekday())

    workdays = ((end_aligned - start_aligned).days // 7) * 5 + 1

    d = start_date
    while d < end_date:
        if d.weekday() < 5:               # Mon–Fri
            workdays += 1
        d += timedelta(days=1)

    return workdays
# ------------------------------------------------------------------ #
# 2. Documentation pivot                                             #
# ------------------------------------------------------------------ #
def build_documentation(aging_df: pd.DataFrame,
                        bin_df:   pd.DataFrame) -> pd.DataFrame:
    merged = aging_df.merge(bin_df, how="left", on="Status")
    pivot  = (pd
              .crosstab(merged["Account_No"], merged["Doc_Status"])
              .reset_index())
    return pivot
# ------------------------------------------------------------------ #
# 3. Name Screening pivot                                            #
# ------------------------------------------------------------------ #
def build_name_screening(aging_df: pd.DataFrame,
                         bin1_df:  pd.DataFrame) -> pd.DataFrame:
    merged = aging_df.merge(bin1_df, how="left", on="Status_screening")
    merged["NS_Status"] = merged["NS_Status"].fillna("Not Updated")
    pivot  = (pd
              .crosstab(merged["Account_No"], merged["NS_Status"])
              .reset_index())
    return pivot
# ------------------------------------------------------------------ #
# 4. Current_Status                                                  #
# ------------------------------------------------------------------ #
def build_current_status(aging_df: pd.DataFrame) -> pd.DataFrame:
    # make sure date columns are datetime64
    for col in ["Date",
                "Focus List Entering Date",
                "Latest Focus Week"]:
        aging_df[col] = pd.to_datetime(aging_df[col], errors="coerce")

    today = pd.Timestamp("today").normalize()

    # calculate Days_Open (same formula as Access, minus 2)
    aging_df["Days_Open"] = aging_df["Focus List Entering Date"].apply(
        lambda d: np.nan if pd.isna(d) else count_workdays_vba(d, today) - 2
    )

    # sort so that groupby('.last') picks the latest record
    latest = (aging_df
              .sort_values("Date")
              .groupby("Account_No")
              .last()
              .reset_index())

    # rename to match Access aliases
    latest = latest.rename(columns={
        "Date":                     "LastOfDate",
        "Status":                   "LastOfStatus",
        "Status_screening":         "LastOfStatus_screening",
        "Priority":                 "LastOfPriority",
        "Focus List Entering Date": "LastOfFocus List Entering Date",
        "Latest Focus Week":        "LastOfLatest Focus Week"
    })

    # apply HAVING filter from Access
    excluded = ["Cancelled",
                "KYC Completed",
                "KYC Completed with Doc Deficiency",
                "On Hold",
                "Pending EAM/Introducer Agreement"]

    current = latest[
        (~latest["LastOfStatus"].isin(excluded)) &
        (latest["LastOfPriority"].isin(["Focus", "VIP"])) &
        (latest["LastOfLatest Focus Week"] >= today - pd.DateOffset(months=1))
    ].copy()

    return current
# ------------------------------------------------------------------ #
# 5. Final Aging table                                               #
# ------------------------------------------------------------------ #
def build_aging_table(aging_df: pd.DataFrame,
                      bin_df:   pd.DataFrame,
                      bin1_df:  pd.DataFrame) -> pd.DataFrame:
    cur  = build_current_status(aging_df)
    doc  = build_documentation(aging_df, bin_df)
    nsc  = build_name_screening(aging_df, bin1_df)

    # merge like Access (RIGHT joins in opposite order ≈ LEFT here)
    final = (cur
             .merge(doc, how="left", on="Account_No")
             .merge(nsc, how="left", on="Account_No"))

    # Add the two constant label columns so column order matches Access
    final.insert(7, "Documentation",  "Documentation")
    final.insert(final.columns.get_loc("Documentation") +
                 len(doc.columns) + 1,
                 "Name_Screening", "Name Screening")

    # fill NaNs coming from pivots with 0
    pivot_cols = [c for c in final.columns
                  if c not in cur.columns
                  and c not in ["Documentation", "Name_Screening"]]
    final[pivot_cols] = final[pivot_cols].fillna(0).astype(int)

    # order by Days_Open (Total_Days_Aging)
    final = final.sort_values("Days_Open", ascending=False, na_position="last")

    # rename for Access‑style heading
    final = final.rename(columns={
        "LastOfDate":                      "Date",
        "Account_No":                      "Account_ID",
        "Days_Open":                       "Total_Days_Aging",
        "LastOfStatus":                    "Latest_Doc_Status",
        "LastOfStatus_screening":          "Latest_Name_Screening_Status",
        "LastOfFocus List Entering Date":  "Date_Enter_Focus_List",
        "LastOfLatest Focus Week":         "Lastest_Focus_Week"
    })

    # re‑index for a tidy output
    final = final.reset_index(drop=True)
    return final
# ------------------------------------------------------------------ #
# 6. Example driver (commented)                                      #
# ------------------------------------------------------------------ #
# if __name__ == "__main__":
#     # aging_df, bin_df, bin1_df must already be created / loaded
#     aging_tbl = build_aging_table(aging_df, bin_df, bin1_df)
#     print(aging_tbl.head())