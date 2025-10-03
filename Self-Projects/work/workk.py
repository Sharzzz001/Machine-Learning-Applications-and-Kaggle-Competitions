import pandas as pd
import re

# -----------------------
# LOAD your data into `df` (replace with your path)
# -----------------------
# df = pd.read_excel("active_test.xlsx", sheet_name="Cleaned_Data")
df = df.copy()

# -----------------------
# Ensure expected columns and find notes column
# -----------------------
if "Account Name" in df.columns and "Account" not in df.columns:
    df.rename(columns={"Account Name": "Account"}, inplace=True)

if "Account subtitle" not in df.columns:
    df["Account subtitle"] = ""

note_cols = [c for c in df.columns if "note" in c.lower()]
note_col = note_cols[0] if note_cols else "Note Block BP Status"

# -----------------------
# 1) Normalise remarks
# -----------------------
def normalize_remark(r):
    if pd.isna(r):
        return r
    s = str(r).strip()
    low = s.lower()
    if low.startswith("dormant"):
        return "Dormant"
    if "total block" in low or "total blocking" in low:
        return "Total Blocking"
    if "transfer" in low and "block" in low:
        return "Blocked for Transfer Transactions"
    return s

df["Remark"] = df["Remark"].apply(normalize_remark)

# -----------------------
# 2) Combine notes + account subtitle map
# -----------------------
def combine_notes(series: pd.Series) -> str:
    texts = [str(x).strip() for x in series.dropna().astype(str)]
    texts = [t for t in texts if t]
    seen = set()
    out = []
    for t in texts:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return " || ".join(out)

subtitle_map = (
    df.groupby("Account", sort=False)["Account subtitle"]
      .apply(lambda s: s.dropna().astype(str).iloc[0] if s.dropna().shape[0] > 0 else "")
      .reset_index()
      .rename(columns={"Account subtitle": "Account_subtitle"})
)

# -----------------------
# 3) Aggregate per account
# -----------------------
agg = (
    df.groupby("Account", sort=False)
      .agg({
          "Remark": lambda x: sorted(set(x.dropna().astype(str))),
          note_col: combine_notes
      })
      .reset_index()
      .rename(columns={note_col: "Notes"})
)

agg = agg.merge(subtitle_map, on="Account", how="left")
agg["Account_subtitle"] = agg["Account_subtitle"].fillna("")
agg["RemarkCombo"] = agg["Remark"].apply(lambda lst: " + ".join(lst) if lst else "(No Remark)")

# -----------------------
# 4) Flags: dormant refinement, UC, DLA, NTS
# -----------------------
nts_accounts = ["A123", "B456"]   # <<<<< replace with your list

agg["is_dormant"] = agg["Remark"].apply(lambda r: len(r) == 1 and r[0] == "Dormant")
agg["is_uc"] = agg["Account_subtitle"].astype(str).str.contains(r"\[UC\]", case=False, na=False)
agg["is_dla"] = agg["Notes"].astype(str).str.contains("DLA", case=False, na=False)
agg["is_nts"] = agg["Account"].isin(nts_accounts)

# counts for reporting
dormant_count = int(agg.loc[agg["is_dormant"], "Account"].nunique())
uc_count = int(agg.loc[agg["is_uc"], "Account"].nunique())
dla_count = int(agg.loc[agg["is_dla"], "Account"].nunique())
nts_count = int(agg.loc[agg["is_nts"], "Account"].nunique())

# mask for exclusion
mask_exclude = agg["is_dormant"] | agg["is_uc"] | agg["is_dla"]

# subset for categorisation (exclude dormant-only, uc, dla)
agg_cat = agg.loc[~mask_exclude].copy()

# -----------------------
# 5) Keyword map
# -----------------------
keyword_map = {
    "Total Blocking": {
        "Overdue RR": ["overdue rr"],
        "IRPQ Attestation": ["irpq attestation", "irpq"],
        "Doc deficiency": ["doc deficiency"],
    },
    "Blocked for Transfer Transactions": {
        "Initial funding": ["initial funding"],
        "Overdue RR": ["overdue rr"],
        "Expired document": ["expired document"],
        "Block from 3pp": ["3pp", "3rd party", "third party"],
    },
}

# -----------------------
# 6) Categorisation
# -----------------------
def categories_for_account(row):
    reason_text = str(row["Notes"]).lower().strip()
    matches = []
    for remark in row["Remark"]:
        if remark not in keyword_map:
            continue
        if reason_text == "":
            matches.append(f"{remark} - Blank")
            continue
        found = False
        for cat_name, kw_list in keyword_map[remark].items():
            for kw in kw_list:
                if kw.lower() in reason_text:
                    matches.append(f"{remark} - {cat_name}")
                    found = True
                    break
        if not found:
            matches.append(f"{remark} - Uncategorized")
    seen, out = set(), []
    for m in matches:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out

agg_cat["Categories"] = agg_cat.apply(categories_for_account, axis=1)

# -----------------------
# 7) Explode categorised data
# -----------------------
exploded = agg_cat.explode("Categories").copy()
exploded = exploded.dropna(subset=["Categories"])
exploded = exploded.rename(columns={"Categories": "Category"})
exploded = exploded[["Account", "RemarkCombo", "Category", "Notes", "is_nts"]].reset_index(drop=True)

# -----------------------
# 8) Pivot
# -----------------------
pivot = exploded.pivot_table(
    index="Category",
    columns="RemarkCombo",
    values="Account",
    aggfunc=lambda x: x.nunique(),
    fill_value=0
)

# add NTS column
nts_subset = exploded[exploded["is_nts"]].copy()
if not nts_subset.empty:
    nts_pivot = nts_subset.pivot_table(
        index="Category",
        values="Account",
        aggfunc=lambda x: x.nunique(),
        fill_value=0
    )
    pivot["NTS"] = nts_pivot

pivot["Total"] = pivot.sum(axis=1)

# -----------------------
# 9) Remark combo distribution
# -----------------------
remark_combo_dist = (
    agg["RemarkCombo"].value_counts().reset_index()
    .rename(columns={"index": "RemarkCombo", "RemarkCombo": "Unique_Account_Count"})
)
remark_combo_dist.columns = ["RemarkCombo", "Unique_Account_Count"]
remark_combo_dist["Pct_of_Total"] = ((remark_combo_dist["Unique_Account_Count"] / agg.shape[0]) * 100).round(2)

# -----------------------
# 10) Summary values
# -----------------------
total_unique_accounts = int(agg["Account"].nunique())
total_reasons = int(pivot["Total"].sum())

print("Total unique accounts:", total_unique_accounts)
print("Total reasons (grand total of pivot):", total_reasons)
print("Dormant-only excluded:", dormant_count)
print("UC excluded:", uc_count)
print("DLA excluded:", dla_count)
print("NTS accounts:", nts_count)

# -----------------------
# 11) Export to Excel
# -----------------------
out_filename = "remark_combinations_output.xlsx"

def autofit_columns(writer, df, sheet_name):
    worksheet = writer.sheets[sheet_name]
    for idx, col in enumerate(df.columns):
        series = df[col].astype(str)
        max_len = max(series.map(len).max(), len(str(col)))
        worksheet.set_column(idx, idx, max_len + 2)

with pd.ExcelWriter(out_filename, engine="xlsxwriter") as writer:
    pivot.to_excel(writer, sheet_name="Pivot_Overview", startrow=0)
    worksheet = writer.sheets["Pivot_Overview"]

    nrows_pivot = pivot.shape[0] + 1
    insert_row = nrows_pivot + 2

    worksheet.write(insert_row, 0, "Total unique accounts:")
    worksheet.write(insert_row, 1, total_unique_accounts)

    worksheet.write(insert_row + 1, 0, "Total reasons for blocked accounts (grand total of pivot):")
    worksheet.write(insert_row + 1, 1, total_reasons)

    worksheet.write(insert_row + 3, 0, "Dormant-only accounts excluded from categorization:")
    worksheet.write(insert_row + 3, 1, dormant_count)

    worksheet.write(insert_row + 4, 0, "Unclaimed accounts ([UC]) excluded from categorization:")
    worksheet.write(insert_row + 4, 1, uc_count)

    worksheet.write(insert_row + 5, 0, "DLA accounts excluded from categorization:")
    worksheet.write(insert_row + 5, 1, dla_count)

    worksheet.write(insert_row + 6, 0, "NTS accounts (treated separately, included in pivot):")
    worksheet.write(insert_row + 6, 1, nts_count)

    dist_start = insert_row + 8
    remark_combo_dist.to_excel(writer, sheet_name="Pivot_Overview", startrow=dist_start, index=False)

    autofit_columns(writer, pivot.reset_index(), "Pivot_Overview")
    autofit_columns(writer, remark_combo_dist, "Pivot_Overview")

print(f"Saved: {out_filename}")