"""
Purpose:
--------
Build per-UID document and screening status ageing from daily SharePoint snapshots
stored in an Access database, using consolidated status mappings.

Output:
-------
One row per UID with:
- Total ageing per consolidated Doc status
- Total ageing per consolidated NS status
- Latest Doc / NS status and their active ageing
- Latest non-null business columns (Power BI ready)

Authoritative rules:
--------------------
- Status change only when consolidated value changes
- Blank status treated as literal 'nan'
- Business days ageing using numpy busday_count
- Snapshot is EOD → start date included
- UID = Request Title + Review Type + Trigger Date
"""

# =========================
# Imports
# =========================
import pandas as pd
import numpy as np
import pyodbc

# =========================
# CONFIGURATION
# =========================

ACCESS_DB_PATH = r"D:\path\to\your_snapshot.accdb"
ACCESS_TABLE_NAME = "YourSnapshotTable"

MAPPING_FILE_PATH = r"D:\path\to\status_mapping.xlsx"

DOC_STATUS_COL = "Documents Ready for Review"
NS_STATUS_COL  = "Screenings"

FILE_DATE_COL = "file_date"

UID_COLS = ["Request Title", "Review Type", "Trigger Date"]

FINAL_STATIC_COLUMNS = [
    "Sales Code",
    "Risk Category",
    "Account Type",
    "Classification",
    "Due Date",
    "Client Name",
    "ekycID"
]

OUTPUT_FILE = r"D:\path\to\final_status_ageing.xlsx"

# =========================
# READ ACCESS DATABASE
# =========================

conn = pyodbc.connect(
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    f"DBQ={ACCESS_DB_PATH};"
)

df = pd.read_sql(f"SELECT * FROM [{ACCESS_TABLE_NAME}]", conn)
conn.close()

# =========================
# DATA TYPE NORMALIZATION
# =========================

df[FILE_DATE_COL] = pd.to_datetime(df[FILE_DATE_COL])
df["Trigger Date"] = pd.to_datetime(df["Trigger Date"])

# =========================
# UID CREATION
# =========================

df["uid"] = (
    df["Request Title"].astype(str) + "|" +
    df["Review Type"].astype(str) + "|" +
    df["Trigger Date"].dt.strftime("%Y-%m-%d")
)

# =========================
# LOAD STATUS MAPPINGS
# =========================

doc_map_df = pd.read_excel(MAPPING_FILE_PATH, sheet_name="Doc_Status")
ns_map_df  = pd.read_excel(MAPPING_FILE_PATH, sheet_name="NS_Status")

DOC_MAP = dict(zip(doc_map_df["Value"], doc_map_df["Consolidated Doc Status"]))
NS_MAP  = dict(zip(ns_map_df["Value"], ns_map_df["Consolidated NS Status"]))

# =========================
# STATUS CONSOLIDATION
# =========================

def consolidate_status(series, mapping):
    out = series.map(mapping)
    out = out.where(out.notna(), series)
    return out.fillna("nan")

df["doc_status"] = consolidate_status(df[DOC_STATUS_COL], DOC_MAP)
df["ns_status"]  = consolidate_status(df[NS_STATUS_COL], NS_MAP)

# =========================
# STATUS INTERVAL BUILDER
# =========================

def build_status_intervals(df, status_col):
    df = df.sort_values(["uid", FILE_DATE_COL]).copy()

    df["prev_status"] = df.groupby("uid")[status_col].shift()
    df["status_change"] = (
        df["prev_status"].isna() |
        (df[status_col] != df["prev_status"])
    )

    intervals = df[df["status_change"]].copy()
    intervals["start_date"] = intervals[FILE_DATE_COL]

    intervals["end_date"] = (
        intervals.groupby("uid")["start_date"]
        .shift(-1)
        .sub(pd.Timedelta(days=1))
    )

    last_file_date = df.groupby("uid")[FILE_DATE_COL].max()
    intervals["end_date"] = intervals["end_date"].fillna(
        intervals["uid"].map(last_file_date)
    )

    intervals["ageing"] = np.busday_count(
        intervals["start_date"].values.astype("datetime64[D]"),
        (intervals["end_date"] + pd.Timedelta(days=1)).values.astype("datetime64[D]")
    )

    return intervals[["uid", status_col, "start_date", "end_date", "ageing"]]

# =========================
# BUILD DOC & NS INTERVALS
# =========================

doc_intervals = build_status_intervals(df, "doc_status")
ns_intervals  = build_status_intervals(df, "ns_status")

# =========================
# TOTAL AGEING PER STATUS
# =========================

doc_pivot = (
    doc_intervals
    .groupby(["uid", "doc_status"])["ageing"]
    .sum()
    .unstack(fill_value=0)
    .add_prefix("doc_status_")
)

ns_pivot = (
    ns_intervals
    .groupby(["uid", "ns_status"])["ageing"]
    .sum()
    .unstack(fill_value=0)
    .add_prefix("ns_status_")
)

# =========================
# LATEST STATUS + ACTIVE AGEING
# =========================

latest_doc = (
    doc_intervals
    .sort_values(["uid", "end_date"])
    .groupby("uid")
    .tail(1)
    .set_index("uid")
)

latest_ns = (
    ns_intervals
    .sort_values(["uid", "end_date"])
    .groupby("uid")
    .tail(1)
    .set_index("uid")
)

latest_status_df = pd.DataFrame(index=latest_doc.index)
latest_status_df["Latest Doc Status"] = latest_doc["doc_status"]
latest_status_df["Latest Doc Status Ageing"] = latest_doc["ageing"]
latest_status_df["Latest NS Status"] = latest_ns["ns_status"]
latest_status_df["Latest NS Status Ageing"] = latest_ns["ageing"]

# =========================
# STATIC BUSINESS COLUMNS
# =========================

static_df = (
    df.sort_values(FILE_DATE_COL)
      .groupby("uid")[FINAL_STATIC_COLUMNS]
      .last()
)

# =========================
# FINAL DATASET
# =========================

final_df = (
    doc_pivot
    .join(ns_pivot, how="outer")
    .join(latest_status_df, how="left")
    .join(static_df, how="left")
    .reset_index()
)

# =========================
# EXPORT
# =========================

final_df.to_excel(OUTPUT_FILE, index=False)

print("Status ageing build completed successfully.")
print(f"Rows created: {len(final_df)}")