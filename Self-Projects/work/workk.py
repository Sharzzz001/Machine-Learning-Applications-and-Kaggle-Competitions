# Paste into a Jupyter cell and run
import pandas as pd
import re

# -----------------------
# LOAD your data into `df` (edit path/sheet)
# -----------------------
# df = pd.read_excel("active_test.xlsx", sheet_name="Cleaned_Data")
# For safety assume df exists in memory; otherwise uncomment above

# Make a working copy
df = df.copy()

# -----------------------
# Basic columns detection / normalization
# -----------------------
if "Account Name" in df.columns and "Account" not in df.columns:
    df.rename(columns={"Account Name": "Account"}, inplace=True)

if "Account subtitle" not in df.columns:
    df["Account subtitle"] = ""

# find notes column (first column containing 'note')
note_cols = [c for c in df.columns if "note" in c.lower()]
note_col = note_cols[0] if note_cols else "Note Block BP Status"

# Ensure Account is string for startswith checks
df["Account"] = df["Account"].astype(str)

# -----------------------
# 1) Normalize remarks (so 'Dormant since <date>' -> 'Dormant', etc.)
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
# 2) Combine notes per account (dedupe & preserve order)
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

# canonical account subtitle per account (first non-null)
subtitle_map = (
    df.groupby("Account", sort=False)["Account subtitle"]
      .apply(lambda s: s.dropna().astype(str).iloc[0] if s.dropna().shape[0] > 0 else "")
      .reset_index()
      .rename(columns={"Account subtitle": "Account_subtitle"})
)

# -----------------------
# 3) Aggregate per account: unique remark list + combined notes
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
# 4) Flags
#    - is_dormant: only Dormant-only (exactly one remark and it is Dormant)
#    - is_uc: Account_subtitle contains [UC]
#    - is_dla: Notes contains 'DLA'
#    - is_nonclient: Account starts with 3,4,5 (string)
#    - is_nts: list provided by user; these should be included and get own NTS pivot column & sheet
# -----------------------
# Provide your NTS account list here (strings)
nts_accounts = ["A123", "B456"]   # <-- REPLACE with your actual NTS account IDs (strings)

def is_nonclient_fn(acc):
    # treat NaNs/empties safely
    s = str(acc).strip()
    return s.startswith(("3", "4", "5"))

agg["is_dormant"] = agg["Remark"].apply(lambda r: (len(r) == 1 and str(r[0]) == "Dormant"))
agg["is_uc"] = agg["Account_subtitle"].astype(str).str.contains(r"\[UC\]", case=False, na=False)
agg["is_dla"] = agg["Notes"].astype(str).str.contains("DLA", case=False, na=False)
agg["is_nonclient"] = agg["Account"].apply(is_nonclient_fn)
agg["is_nts"] = agg["Account"].isin([str(x) for x in nts_accounts])

# counts for reporting
dormant_count = int(agg.loc[agg["is_dormant"], "Account"].nunique())
uc_count = int(agg.loc[agg["is_uc"], "Account"].nunique())
dla_count = int(agg.loc[agg["is_dla"], "Account"].nunique())
nonclient_count = int(agg.loc[agg["is_nonclient"], "Account"].nunique())
nts_count = int(agg.loc[agg["is_nts"], "Account"].nunique())

# mask to EXCLUDE from categorization (dormant-only, uc, dla, nonclient)
mask_exclude = agg["is_dormant"] | agg["is_uc"] | agg["is_dla"] | agg["is_nonclient"]

# subset included for categorisation (includes NTS accounts that are not excluded by above rules)
agg_cat = agg.loc[~mask_exclude].copy()

# -----------------------
# 5) YOUR keyword_map (replace/extend with your full mapping)
# -----------------------
keyword_map = {
    "Total Blocking": {
        "Overdue RR": ["overdue rr"],
        "IRPQ Attestation": ["irpq attestation", "irpq"],
        "Doc deficiency": ["doc deficiency"],
        # ... add all categories / keywords
    },
    "Blocked for Transfer Transactions": {
        "Initial funding": ["initial funding"],
        "Overdue RR": ["overdue rr"],
        "Expired document": ["expired document"],
        "Block from 3pp": ["3pp", "3rd party", "third party"],
        # ... add more
    },
    # Add other remark types & their keyword mappings if required
}

# -----------------------
# 6) Categorize: check ALL keywords for each remark on included accounts
# -----------------------
def categories_for_account(row):
    reason_text = str(row["Notes"]).lower().strip()
    matches = []
    for remark in row["Remark"]:
        if remark not in keyword_map:
            # skip remark types with no keyword map
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

    # dedupe preserve order
    seen = set(); out = []
    for m in matches:
        if m not in seen:
            seen.add(m); out.append(m)
    return out

agg_cat["Categories"] = agg_cat.apply(categories_for_account, axis=1)

# -----------------------
# 7) Explode included categorised data (this is the exact input to the pivot)
# -----------------------
exploded = agg_cat.explode("Categories").copy()
exploded = exploded.dropna(subset=["Categories"])
exploded = exploded.rename(columns={"Categories": "Category"})
# include NTS flag in exploded for building NTS pivot column and sheet
exploded = exploded[["Account", "RemarkCombo", "Category", "Notes", "is_nts"]].reset_index(drop=True)

# -----------------------
# 8) Build pivot: rows=Category, cols=RemarkCombo (counts = unique accounts)
# -----------------------
pivot = exploded.pivot_table(
    index="Category",
    columns="RemarkCombo",
    values="Account",
    aggfunc=lambda x: x.nunique(),
    fill_value=0
)

# Add NTS column (count unique NTS accounts per category)
nts_subset = exploded[exploded["is_nts"]].copy()
if not nts_subset.empty:
    nts_counts = nts_subset.groupby("Category")["Account"].nunique()
    # Add 'NTS' column aligned with pivot index (fill missing with 0)
    pivot["NTS"] = pivot.index.to_series().map(lambda idx: int(nts_counts.get(idx, 0)))
else:
    pivot["NTS"] = 0

# Final totals column (sum across columns)
pivot["Total"] = pivot.sum(axis=1)

# -----------------------
# 9) Remark combo distribution for included accounts excluding NTS (we'll treat NTS separately)
# -----------------------
included_non_nts = agg_cat.loc[~agg_cat["is_nts"]].copy()
remark_combo_dist = (
    included_non_nts["RemarkCombo"]
    .value_counts()
    .reset_index()
    .rename(columns={"index": "RemarkCombo", "RemarkCombo": "Unique_Account_Count"})
)
remark_combo_dist.columns = ["RemarkCombo", "Unique_Account_Count"]
remark_combo_dist["Pct_of_Included_NonNTS"] = ((remark_combo_dist["Unique_Account_Count"] / max(1, included_non_nts.shape[0])) * 100).round(2)

# Also compute a small table for NTS remark combos (optional)
nts_combo_counts = (
    agg_cat[agg_cat["is_nts"]]["RemarkCombo"]
    .value_counts()
    .reset_index()
    .rename(columns={"index": "RemarkCombo", "RemarkCombo": "NTS_Unique_Account_Count"})
)

# -----------------------
# 10) Totals for reporting
# -----------------------
total_unique_accounts = int(agg["Account"].nunique())   # includes excluded
total_reasons = int(pivot["Total"].sum())              # count across included accounts

# -----------------------
# 11) Prepare sheets and Combo_Index. We'll create per-combo sheets from included_non_nts combos (exclude NTS),
#       PLUS a dedicated 'NTS' sheet for NTS accounts (they are included in categorization)
# -----------------------
out_filename = "remark_combinations_output_with_NTS_nonclient.xlsx"

def autofit_columns(writer, df, sheet_name):
    worksheet = writer.sheets[sheet_name]
    for idx, col in enumerate(df.columns):
        try:
            series = df[col].astype(str)
            max_len = max(series.map(len).max(), len(str(col)))
        except Exception:
            max_len = len(str(col))
        worksheet.set_column(idx, idx, max_len + 2)

# combos to create sheets for (only included_non_nts combos; this keeps NTS separate)
combo_list_included = included_non_nts["RemarkCombo"].unique().tolist()

combo_map = []

with pd.ExcelWriter(out_filename, engine="xlsxwriter") as writer:
    # Pivot_Overview
    pivot.to_excel(writer, sheet_name="Pivot_Overview", startrow=0)
    worksheet = writer.sheets["Pivot_Overview"]
    worksheet.freeze_panes(1, 0)

    # compute where to write summary lines
    nrows_pivot = pivot.shape[0] + 1
    insert_row = nrows_pivot + 2

    # Summary sentences
    worksheet.write(insert_row, 0, "Total unique accounts:")
    worksheet.write(insert_row, 1, total_unique_accounts)

    worksheet.write(insert_row + 1, 0, "Total reasons for blocked accounts (grand total of pivot):")
    worksheet.write(insert_row + 1, 1, int(total_reasons))

    worksheet.write(insert_row + 3, 0, "Dormant-only accounts excluded from categorization:")
    worksheet.write(insert_row + 3, 1, dormant_count)

    worksheet.write(insert_row + 4, 0, "Unclaimed accounts ([UC]) excluded from categorization:")
    worksheet.write(insert_row + 4, 1, uc_count)

    worksheet.write(insert_row + 5, 0, "DLA accounts excluded from categorization:")
    worksheet.write(insert_row + 5, 1, dla_count)

    worksheet.write(insert_row + 6, 0, "Non-client / Broker accounts (start with 3/4/5) excluded:")
    worksheet.write(insert_row + 6, 1, nonclient_count)

    worksheet.write(insert_row + 7, 0, "NTS accounts (treated as separate combo, included in categorization):")
    worksheet.write(insert_row + 7, 1, nts_count)

    # write remark combo distribution for included_non_nts
    dist_start = insert_row + 9
    remark_combo_dist.to_excel(writer, sheet_name="Pivot_Overview", startrow=dist_start, index=False)

    # also write the NTS combo counts under that (if present) - appended below distribution
    if not nts_combo_counts.empty:
        nts_start = dist_start + remark_combo_dist.shape[0] + 2
        pd.DataFrame({"RemarkCombo": ["NTS (summary)"], "NTS_Unique_Account_Count": [nts_count]}).to_excel(writer, sheet_name="Pivot_Overview", startrow=nts_start, index=False)

    # Autofit pivot and distribution views
    autofit_columns(writer, pivot.reset_index(), "Pivot_Overview")
    autofit_columns(writer, remark_combo_dist, "Pivot_Overview")

    # Account_Aggregated (all accounts, with flags)
    agg.to_excel(writer, sheet_name="Account_Aggregated", index=False)
    autofit_columns(writer, agg, "Account_Aggregated")
    writer.sheets["Account_Aggregated"].freeze_panes(1, 0)

    # Account_Category (exploded used to build pivot) - this contains only included (agg_cat) rows
    exploded.to_excel(writer, sheet_name="Account_Category", index=False)
    autofit_columns(writer, exploded, "Account_Category")
    writer.sheets["Account_Category"].freeze_panes(1, 0)

    # Create sheets for included combos (non-NTS)
    for i, combo in enumerate(combo_list_included, start=1):
        sheet_name = f"Combo_{i}"
        subset = exploded[exploded["RemarkCombo"] == combo].copy()
        # if there are no rows for that combo, write empty df with the same columns
        if subset.empty:
            subset = pd.DataFrame(columns=exploded.columns)
        # remove NTS rows from these combo sheets (we keep NTS in its own sheet)
        subset_non_nts = subset.loc[~subset["is_nts"]].copy()
        # write sheet
        subset_non_nts.to_excel(writer, sheet_name=sheet_name, index=False)
        autofit_columns(writer, subset_non_nts, sheet_name)
        writer.sheets[sheet_name].freeze_panes(1, 0)
        # mapping info (counts)
        combo_map.append({
            "Combo_Sheet": sheet_name,
            "RemarkCombo": combo,
            "Unique_Accounts_All": int(agg.loc[agg["RemarkCombo"] == combo, "Account"].nunique()),
            "Unique_Accounts_IncludedForCategorization": int(agg_cat.loc[agg_cat["RemarkCombo"] == combo, "Account"].nunique()),
            "Unique_Accounts_Excluded": int(agg.loc[(agg["RemarkCombo"] == combo) & mask_exclude, "Account"].nunique()),
            "NTS_Accounts_in_Combo": int(agg_cat[(agg_cat["RemarkCombo"] == combo) & agg_cat["is_nts"], "Account"].nunique())
        })

    # NTS sheet (all NTS accounts that are included in categorisation)
    nts_sheet_df = exploded[exploded["is_nts"]].copy()
    if nts_sheet_df.empty:
        nts_sheet_df = pd.DataFrame(columns=exploded.columns)
    nts_sheet_df.to_excel(writer, sheet_name="NTS", index=False)
    autofit_columns(writer, nts_sheet_df, "NTS")
    writer.sheets["NTS"].freeze_panes(1, 0)
    # Add mapping entry for NTS
    combo_map.append({
        "Combo_Sheet": "NTS",
        "RemarkCombo": "NTS (separate combo)",
        "Unique_Accounts_All": int(agg[agg["is_nts"], "Account"].nunique()) if "is_nts" in agg.columns else 0,
        "Unique_Accounts_IncludedForCategorization": int(agg_cat[agg_cat["is_nts"], "Account"].nunique()) if "is_nts" in agg_cat.columns else 0,
        "Unique_Accounts_Excluded": 0,
        "NTS_Accounts_in_Combo": int(agg_cat[agg_cat["is_nts"], "Account"].nunique()) if "is_nts" in agg_cat.columns else 0
    })

    # Combo_Index sheet
    combo_df = pd.DataFrame(combo_map)
    if combo_df.empty:
        combo_df = pd.DataFrame(columns=["Combo_Sheet", "RemarkCombo", "Unique_Accounts_All", "Unique_Accounts_IncludedForCategorization", "Unique_Accounts_Excluded", "NTS_Accounts_in_Combo"])
    combo_df.to_excel(writer, sheet_name="Combo_Index", index=False)
    autofit_columns(writer, combo_df, "Combo_Index")
    writer.sheets["Combo_Index"].freeze_panes(1, 0)

    # Excluded sheets for inspection
    excluded_all = agg.loc[mask_exclude].copy()
    excluded_all.to_excel(writer, sheet_name="Excluded_All", index=False)
    autofit_columns(writer, excluded_all, "Excluded_All")
    writer.sheets["Excluded_All"].freeze_panes(1, 0)

    excluded_dormant = agg.loc[agg["is_dormant"]].copy()
    excluded_dormant.to_excel(writer, sheet_name="Excluded_DormantOnly", index=False)
    autofit_columns(writer, excluded_dormant, "Excluded_DormantOnly")
    writer.sheets["Excluded_DormantOnly"].freeze_panes(1, 0)

    excluded_uc = agg.loc[agg["is_uc"]].copy()
    excluded_uc.to_excel(writer, sheet_name="Excluded_UC", index=False)
    autofit_columns(writer, excluded_uc, "Excluded_UC")
    writer.sheets["Excluded_UC"].freeze_panes(1, 0)

    excluded_dla = agg.loc[agg["is_dla"]].copy()
    excluded_dla.to_excel(writer, sheet_name="Excluded_DLA", index=False)
    autofit_columns(writer, excluded_dla, "Excluded_DLA")
    writer.sheets["Excluded_DLA"].freeze_panes(1, 0)

    excluded_nonclient = agg.loc[agg["is_nonclient"]].copy()
    excluded_nonclient.to_excel(writer, sheet_name="Excluded_NonClient", index=False)
    autofit_columns(writer, excluded_nonclient, "Excluded_NonClient")
    writer.sheets["Excluded_NonClient"].freeze_panes(1, 0)

print(f"Saved file: {out_filename}")
print("Total unique accounts (all):", total_unique_accounts)
print("Total reasons (grand total pivot — included accounts):", total_reasons)
print("Dormant-only excluded:", dormant_count)
print("UC excluded:", uc_count)
print("DLA excluded:", dla_count)
print("Non-client excluded:", nonclient_count)
print("NTS accounts included:", nts_count)