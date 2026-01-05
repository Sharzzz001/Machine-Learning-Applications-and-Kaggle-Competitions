import pandas as pd
import numpy as np
from datetime import date

# ---------------------------------------
# USER INPUTS
# ---------------------------------------

ACCESS_TABLE = "RR_SOW_Snapshots"

# Columns you want to carry forward (latest snapshot value)
LATEST_VALUE_COLUMNS = [
    # Example:
    # "Risk",
    # "RM",
    # "GH",
    # "ReviewType"
]

OUTPUT_FILE = "SOW_Ageing_PowerBI.xlsx"

# ---------------------------------------
# LOAD DATA
# ---------------------------------------

# Assuming you already read this from Access
df = sow_df.copy()  # replace with your actual dataframe

# Ensure correct dtypes
df["FileDate"] = pd.to_datetime(df["FileDate"]).dt.date
df["AccountNumber"] = df["AccountNumber"].astype(str)

# ---------------------------------------
# LOAD CONSOLIDATION MAPPING
# ---------------------------------------

# Example structure:
# Value | Consolidated SOW Status
consolidation_df = pd.read_excel("SOW_Status_Consolidation.xlsx")

consolidation_map = dict(
    zip(
        consolidation_df["Value"],
        consolidation_df["Consolidated SOW Status"]
    )
)

# ---------------------------------------
# CREATE FINAL STATUS
# ---------------------------------------

df["FinalStatus"] = df["SOWStatus"].map(consolidation_map)
df["FinalStatus"] = df["FinalStatus"].fillna(df["SOWStatus"])

# ---------------------------------------
# CALCULATE STATUS AGEING
# ---------------------------------------

ageing_records = []

for acc, g in df.groupby("AccountNumber"):
    g = g.sort_values("FileDate").reset_index(drop=True)

    for i in range(len(g)):
        start_date = g.loc[i, "FileDate"]
        status = g.loc[i, "FinalStatus"]

        # Determine end date
        if i + 1 < len(g) and g.loc[i + 1, "FinalStatus"] != status:
            end_date = g.loc[i + 1, "FileDate"]
        else:
            end_date = g.loc[len(g) - 1, "FileDate"] + pd.Timedelta(days=1)

        # Business days (inclusive of start date)
        days = np.busday_count(start_date, end_date)

        if days > 0:
            ageing_records.append({
                "AccountNumber": acc,
                "FinalStatus": status,
                "Ageing": days,
                "IsLatest": i == len(g) - 1
            })

ageing_df = pd.DataFrame(ageing_records)

# ---------------------------------------
# OVERALL AGEING PER STATUS
# ---------------------------------------

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

# ---------------------------------------
# LATEST STATUS & AGEING
# ---------------------------------------

latest_status_df = (
    ageing_df[ageing_df["IsLatest"]]
    .sort_values(["AccountNumber"])
    .drop_duplicates("AccountNumber", keep="last")
    [["AccountNumber", "FinalStatus", "Ageing"]]
    .rename(columns={
        "FinalStatus": "LatestStatus",
        "Ageing": "LatestStatusAgeing"
    })
)

# ---------------------------------------
# LATEST SNAPSHOT VALUES
# ---------------------------------------

latest_snapshot = (
    df.sort_values("FileDate")
      .groupby("AccountNumber", as_index=False)
      .tail(1)
      [["AccountNumber"] + LATEST_VALUE_COLUMNS]
)

# ---------------------------------------
# FINAL DATASET
# ---------------------------------------

final_df = (
    pivot_df
    .reset_index()
    .merge(latest_status_df, on="AccountNumber", how="left")
    .merge(latest_snapshot, on="AccountNumber", how="left")
)

# ---------------------------------------
# EXPORT
# ---------------------------------------

final_df.to_excel(OUTPUT_FILE, index=False)

print(f"Power BI dataset saved to {OUTPUT_FILE}")