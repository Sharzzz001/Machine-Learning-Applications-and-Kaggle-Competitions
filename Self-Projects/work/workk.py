import pandas as pd
import numpy as np

# =====================================================
# USER INPUTS
# =====================================================

# Data already loaded from Access
# df must contain at least:
# AccountNumber, FileDate, SOWStatus
df = sow_df.copy()

# Consolidation mapping file
# Columns: Value, Consolidated SOW Status
consolidation_df = pd.read_excel("SOW_Status_Consolidation.xlsx")

# Columns to carry forward from latest snapshot
LATEST_VALUE_COLUMNS = [
    # Example:
    # "Risk",
    # "RM",
    # "GH",
    # "ReviewType"
]

OUTPUT_FILE = "SOW_Ageing_PowerBI.xlsx"

# =====================================================
# PREPARE DATA
# =====================================================

df["AccountNumber"] = df["AccountNumber"].astype(str)
df["FileDate"] = pd.to_datetime(df["FileDate"]).dt.date

# Build consolidation map
consolidation_map = dict(
    zip(
        consolidation_df["Value"],
        consolidation_df["Consolidated SOW Status"]
    )
)

# Apply consolidation
df["FinalStatus"] = df["SOWStatus"].map(consolidation_map)
df["FinalStatus"] = df["FinalStatus"].fillna(df["SOWStatus"])

# =====================================================
# BUILD STATUS RUNS & AGEING
# =====================================================

records = []

for acc, g in df.groupby("AccountNumber"):
    g = g.sort_values("FileDate").reset_index(drop=True)

    # Identify status changes
    g["IsNewRun"] = g["FinalStatus"] != g["FinalStatus"].shift(1)
    g["RunID"] = g["IsNewRun"].cumsum()

    last_file_date = g["FileDate"].iloc[-1]

    for run_id, r in g.groupby("RunID"):
        status = r["FinalStatus"].iloc[0]
        run_start = r["FileDate"].iloc[0]

        # Determine run end (exclusive)
        if r.index.max() < g.index.max():
            run_end = g.loc[r.index.max() + 1, "FileDate"]
        else:
            # last run → include last snapshot day
            run_end = last_file_date + pd.Timedelta(days=1)

        ageing = np.busday_count(run_start, run_end)

        records.append({
            "AccountNumber": acc,
            "FinalStatus": status,
            "RunStart": run_start,
            "RunEnd": run_end,
            "Ageing": ageing,
            "IsLatestRun": r.index.max() == g.index.max()
        })

ageing_df = pd.DataFrame(records)

# =====================================================
# OVERALL AGEING PER STATUS (BACK & FORTH SUPPORTED)
# =====================================================

overall_ageing = (
    ageing_df
    .groupby(["AccountNumber", "FinalStatus"], as_index=False)["Ageing"]
    .sum()
)

pivot_df = (
    overall_ageing
    .pivot(
        index="AccountNumber",
        columns="FinalStatus",
        values="Ageing"
    )
    .fillna(0)
)

# =====================================================
# LATEST STATUS & LATEST STATUS AGEING
# =====================================================

latest_status_df = (
    ageing_df[ageing_df["IsLatestRun"]]
    [["AccountNumber", "FinalStatus", "Ageing"]]
    .rename(columns={
        "FinalStatus": "LatestStatus",
        "Ageing": "LatestStatusAgeing"
    })
)

# =====================================================
# LATEST SNAPSHOT ATTRIBUTES
# =====================================================

latest_snapshot = (
    df.sort_values("FileDate")
      .groupby("AccountNumber", as_index=False)
      .tail(1)
      [["AccountNumber"] + LATEST_VALUE_COLUMNS]
)

# =====================================================
# FINAL POWER BI DATASET
# =====================================================

final_df = (
    pivot_df
    .reset_index()
    .merge(latest_status_df, on="AccountNumber", how="left")
    .merge(latest_snapshot, on="AccountNumber", how="left")
)

# =====================================================
# EXPORT
# =====================================================

final_df.to_excel(OUTPUT_FILE, index=False)

print(f"Power BI dataset created: {OUTPUT_FILE}")