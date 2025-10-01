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
# Normalize remarks
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
# Combine notes per account (dedupe & preserve order)
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

# canonical subtitle per account (first non-null)
subtitle_map = (
    df.groupby("Account", sort=False)["Account subtitle"]
      .apply(lambda s: s.dropna().astype(str).iloc[0] if s.dropna().shape[0] > 0 else "")
      .reset_index()
      .rename(columns={"Account subtitle": "Account_subtitle"})
)

# -----------------------
# Aggregate per account: remark list + combined notes
# -----------------------
agg = (
    df
    .groupby("Account", sort=False)
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
# Identify exclusion groups
# -----------------------
agg["is_dormant"] = agg["Remark"].apply(lambda r: any("dormant" in str(x).lower() for x in r))
agg["is_uc"] = agg["Account_subtitle"].astype(str).str.contains(r"\[UC\]", case=False, na=False)
agg["is_dla"] = agg["Notes"].astype(str).str.contains("DLA", case=False, na=False)

dormant_count = int(agg.loc[agg["is_dormant"], "Account"].nunique())
uc_count = int(agg.loc[agg["is_uc"], "Account"].nunique())
dla_count = int(agg.loc[agg["is_dla"], "Account"].nunique())

# mask to EXCLUDE from categorization
mask_exclude = agg["is_dormant"] | agg["is_uc"] | agg["is_dla"]

# subset included for categorization
agg_cat = agg.loc[~mask_exclude].copy()

# -----------------------
# keyword_map (replace with your full map)
# -----------------------
keyword_map = {
    "Total Blocking": {
        "Overdue RR": ["overdue rr"],
        "IRPQ Attestation": ["irpq attestation", "irpq"],
        "Doc deficiency": ["doc deficiency"],
        # ... add more
    },
    "Blocked for Transfer Transactions": {
        "Initial funding": ["initial funding"],
        "Overdue RR": ["overdue rr"],
        "Expired document": ["expired document"],
        "Block from 3pp": ["3pp", "3rd party", "third party"],
        # ... add more
    },
}

# -----------------------
# Categorize only agg_cat (included accounts)
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
        found_for_remark = False
        for cat_name, kw_list in keyword_map[remark].items():
            for kw in kw_list:
                if kw and kw.lower() in reason_text:
                    matches.append(f"{remark} - {cat_name}")
                    found_for_remark = True
                    break
        if not found_for_remark:
            matches.append(f"{remark} - Uncategorized")
    # dedupe preserving order
    seen = set(); out = []
    for m in matches:
        if m not in seen:
            seen.add(m); out.append(m)
    return out

agg_cat["Categories"] = agg_cat.apply(categories_for_account, axis=1)

# -----------------------
# Explode (only included accounts)
# -----------------------
exploded = agg_cat.explode("Categories").copy()
exploded = exploded.dropna(subset=["Categories"])
exploded = exploded.rename(columns={"Categories": "Category"})
exploded = exploded[["Account", "RemarkCombo", "Category", "Notes"]].reset_index(drop=True)

# -----------------------
# Pivot (categorisation outputs only)
# -----------------------
pivot = exploded.pivot_table(
    index="Category",
    columns="RemarkCombo",
    values="Account",
    aggfunc=lambda x: x.nunique(),
    fill_value=0
)
pivot["Total"] = pivot.sum(axis=1)

# -----------------------
# Remark combo distribution: use ONLY included accounts (agg_cat)
# -----------------------
remark_combo_dist = (
    agg_cat["RemarkCombo"]
    .value_counts()
    .reset_index()
    .rename(columns={"index": "RemarkCombo", "RemarkCombo": "Unique_Account_Count"})
)
remark_combo_dist.columns = ["RemarkCombo", "Unique_Account_Count"]
# percentage of included accounts
remark_combo_dist["Pct_of_Included"] = ((remark_combo_dist["Unique_Account_Count"] / agg_cat.shape[0]) * 100).round(2)

# -----------------------
# Totals and summary lines
# -----------------------
total_unique_accounts = int(agg["Account"].nunique())       # includes excluded accounts
total_reasons = int(pivot["Total"].sum())                   # categ. reasons (excluded removed)

# -----------------------
# Prepare excluded sheets for review
# -----------------------
excluded_all = agg.loc[mask_exclude].copy()
excluded_dormant = agg.loc[agg["is_dormant"]].copy()
excluded_uc = agg.loc[agg["is_uc"]].copy()
excluded_dla = agg.loc[agg["is_dla"]].copy()

# -----------------------
# Excel export (autofit + frozen headers + combo sheets only include included accounts)
# -----------------------
out_filename = "remark_combinations_output_corrected.xlsx"

def autofit_columns(writer, df, sheet_name):
    worksheet = writer.sheets[sheet_name]
    for idx, col in enumerate(df.columns):
        try:
            series = df[col].astype(str)
            max_len = max(series.map(len).max(), len(str(col)))
        except Exception:
            max_len = len(str(col))
        worksheet.set_column(idx, idx, max_len + 2)

all_combos_included = agg_cat["RemarkCombo"].unique().tolist()

combo_map = []
with pd.ExcelWriter(out_filename, engine="xlsxwriter") as writer:
    # Pivot sheet
    pivot.to_excel(writer, sheet_name="Pivot_Overview", startrow=0)
    worksheet = writer.sheets["Pivot_Overview"]
    worksheet.freeze_panes(1, 0)

    # where to insert summary lines
    nrows_pivot = pivot.shape[0] + 1
    insert_row = nrows_pivot + 2

    # write sentences
    worksheet.write(insert_row, 0, "Total unique accounts:")
    worksheet.write(insert_row, 1, total_unique_accounts)

    worksheet.write(insert_row + 1, 0, "Total reasons for blocked accounts (grand total of pivot):")
    worksheet.write(insert_row + 1, 1, total_reasons)

    worksheet.write(insert_row + 3, 0, "Dormant accounts excluded from categorization:")
    worksheet.write(insert_row + 3, 1, dormant_count)

    worksheet.write(insert_row + 4, 0, "Unclaimed accounts ([UC]) excluded from categorization:")
    worksheet.write(insert_row + 4, 1, uc_count)

    worksheet.write(insert_row + 5, 0, "DLA accounts excluded from categorization:")
    worksheet.write(insert_row + 5, 1, dla_count)

    # remark combo distribution (ONLY included accounts) below those lines
    dist_start = insert_row + 7
    remark_combo_dist.to_excel(writer, sheet_name="Pivot_Overview", startrow=dist_start, index=False)

    # Autofit pivot and distribution
    autofit_columns(writer, pivot.reset_index(), "Pivot_Overview")
    autofit_columns(writer, remark_combo_dist, "Pivot_Overview")

    # write account_aggregated (all accounts)
    agg.to_excel(writer, sheet_name="Account_Aggregated", index=False)
    autofit_columns(writer, agg, "Account_Aggregated")
    writer.sheets["Account_Aggregated"].freeze_panes(1, 0)

    # write exploded data (only included accounts) for reconciliation
    exploded.to_excel(writer, sheet_name="Account_Category", index=False)
    autofit_columns(writer, exploded, "Account_Category")
    writer.sheets["Account_Category"].freeze_panes(1, 0)

    # create per-combo sheets from included accounts ONLY
    for i, combo in enumerate(all_combos_included, start=1):
        sheet_name = f"Combo_{i}"
        expl_subset = exploded[exploded["RemarkCombo"] == combo].copy()
        if expl_subset.empty:
            expl_subset = pd.DataFrame(columns=["Account", "RemarkCombo", "Category", "Notes"])
        # write included-only sheet
        expl_subset.to_excel(writer, sheet_name=sheet_name, index=False)
        autofit_columns(writer, expl_subset, sheet_name)
        writer.sheets[sheet_name].freeze_panes(1, 0)

        # mapping info (counts: all accounts with this combo, included, excluded)
        combo_map.append({
            "Combo_Sheet": sheet_name,
            "RemarkCombo": combo,
            "Unique_Accounts_All": int(agg.loc[agg["RemarkCombo"] == combo, "Account"].nunique()),
            "Unique_Accounts_IncludedForCategorization": int(exploded.loc[exploded["RemarkCombo"] == combo, "Account"].nunique()),
            "Unique_Accounts_Excluded": int(agg.loc[(agg["RemarkCombo"] == combo) & mask_exclude, "Account"].nunique())
        })

    # Combo_Index
    combo_df = pd.DataFrame(combo_map)
    combo_df.to_excel(writer, sheet_name="Combo_Index", index=False)
    autofit_columns(writer, combo_df, "Combo_Index")
    writer.sheets["Combo_Index"].freeze_panes(1, 0)

    # Write excluded sheets for inspection
    excluded_all.to_excel(writer, sheet_name="Excluded_All", index=False)
    autofit_columns(writer, excluded_all, "Excluded_All")
    writer.sheets["Excluded_All"].freeze_panes(1, 0)

    excluded_dormant.to_excel(writer, sheet_name="Excluded_Dormant", index=False)
    autofit_columns(writer, excluded_dormant, "Excluded_Dormant")
    writer.sheets["Excluded_Dormant"].freeze_panes(1, 0)

    excluded_uc.to_excel(writer, sheet_name="Excluded_UC", index=False)
    autofit_columns(writer, excluded_uc, "Excluded_UC")
    writer.sheets["Excluded_UC"].freeze_panes(1, 0)

    excluded_dla.to_excel(writer, sheet_name="Excluded_DLA", index=False)
    autofit_columns(writer, excluded_dla, "Excluded_DLA")
    writer.sheets["Excluded_DLA"].freeze_panes(1, 0)

print(f"Saved corrected file: {out_filename}")
print("Total unique accounts (includes excluded):", total_unique_accounts)
print("Total reasons (pivot grand total — excluded removed):", total_reasons)
print("Dormant excluded:", dormant_count, "UC excluded:", uc_count, "DLA excluded:", dla_count)