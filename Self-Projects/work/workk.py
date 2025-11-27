import pandas as pd
import numpy as np

# Make copies so we don't mutate originals accidentally
rr = rr.copy()
sow = sow.copy()

# 1️⃣ Normalise Due Date / DueDate types
# rr has object; convert to datetime and then date
rr["Due Date"] = pd.to_datetime(rr["Due Date"], errors="coerce").dt.date
# sow already datetime64; just ensure date-only as well
sow["DueDate"] = pd.to_datetime(sow["DueDate"], errors="coerce").dt.date

# 2️⃣ Treat blanks in ekycID as missing
for df, col in [(rr, "ekycID"), (sow, "ekycID")]:
    df[col] = df[col].replace("", np.nan)

# (Optional but recommended) – if sow may have duplicates on ekycID / Title+DueDate,
# decide how to resolve them. Example: keep the last one.
sow_by_ekyc = (
    sow.sort_values("DueDate")
       .drop_duplicates(subset=["ekycID"], keep="last")
)

sow_by_acc_date = (
    sow.sort_values("DueDate")
       .drop_duplicates(subset=["Title", "DueDate"], keep="last")
)

# 3️⃣ First pass – merge on ekycID
rr_merged = rr.merge(
    sow_by_ekyc[["ekycID", "SOWStatus"]],
    on="ekycID",
    how="left",
)

# 4️⃣ Second pass – merge on (Account number + Due Date)
#    Account number columns: rr["Request Title"] ↔ sow["Title"]
rr_merged = rr_merged.merge(
    sow_by_acc_date[["Title", "DueDate", "SOWStatus"]]
        .rename(columns={"SOWStatus": "SOWStatus_by_acc_date"}),
    left_on=["Request Title", "Due Date"],
    right_on=["Title", "DueDate"],
    how="left"
)

# 5️⃣ Coalesce SOWStatus from the two steps
#    Priority: ekycID match first; if NaN, then account+date match
rr_merged["SOWStatus_final"] = rr_merged["SOWStatus"].combine_first(
    rr_merged["SOWStatus_by_acc_date"]
)

# 6️⃣ Clean up helper columns
rr_merged = rr_merged.drop(columns=["Title", "DueDate", "SOWStatus_by_acc_date"])

# If you just want a single SOWStatus column in rr:
rr_merged = rr_merged.rename(columns={"SOWStatus_final": "SOWStatus"})