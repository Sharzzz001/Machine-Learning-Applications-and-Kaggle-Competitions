import pandas as pd
import re

# -----------------------
# LOAD your data into `df` (replace with your path)
# -----------------------
# df = pd.read_excel("active_test.xlsx", sheet_name="Cleaned_Data")
# For safety in interactive runs
df = df.copy()

# -----------------------
# Ensure expected columns and find notes column
# -----------------------
if "Account Name" in df.columns and "Account" not in df.columns:
    df.rename(columns={"Account Name": "Account"}, inplace=True)

# Ensure 'Account subtitle' exists (used for [UC] detection)
if "Account subtitle" not in df.columns:
    df["Account subtitle"] = ""

# Find a notes column (first column with 'note' in its name), fallback to the explicit name
note_cols = [c for c in df.columns if "note" in c.lower()]
note_col = note_cols[0] if note_cols else "Note Block BP Status"

# -----------------------
# 1) Normalise remarks (so "Dormant since <date>" -> "Dormant")
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
# 2) Helper to combine notes per account (dedupe & preserve order)
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

# Extract a canonical account subtitle per account (first non-null if present)
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
    df
    .groupby("Account", sort=False)
    .agg({
        "Remark": lambda x: sorted(set(x.dropna().astype(str))),
        note_col: combine_notes
    })
    .reset_index()
    .rename(columns={note_col: "Notes"})
)

# merge subtitle_map into agg
agg = agg.merge(subtitle_map, on="Account", how="left")
agg["Account_subtitle"] = agg["Account_subtitle"].fillna("")

# Create a stable, order-invariant combo string
agg["RemarkCombo"] = agg["Remark"].apply(lambda lst: " + ".join(lst) if lst else "(No Remark)")

# -----------------------
# 4) Identify exclusion groups (but keep them in the overall counts)
#    - Dormant: any remark == "Dormant"
#    - Unclaimed [UC]: Account_subtitle contains [UC]
#    - DLA: Notes contain 'DLA' (case-insensitive)
# -----------------------
agg["is_dormant"] = agg["Remark"].apply(lambda r: any("dormant" == str(x).lower() or "dormant" in str(x).lower() for x in r))
agg["is_uc"] = agg["Account_subtitle"].astype(str).str.contains(r"\[UC\]", case=False, na=False)
agg["is_dla"] = agg["Notes"].astype(str).str.contains("DLA", case=False, na=False)

# counts for reporting (unique accounts)
dormant_count = int(agg.loc[agg["is_dormant"], "Account"].nunique())
uc_count = int(agg.loc[agg["is_uc"], "Account"].nunique())
dla_count = int(agg.loc[agg["is_dla"], "Account"].nunique())

# mask for accounts to EXCLUDE from categorization
mask_exclude = agg["is_dormant"] | agg["is_uc"] | agg["is_dla"]

# subset that will be categorized
agg_cat = agg.loc[~mask_exclude].copy()

# -----------------------
# 5) YOUR keyword_map (replace/extend with your full mapping)
#    Keys must match the normalized remark strings above.
# -----------------------
keyword_map = {
    "Total Blocking": {
        "Overdue RR": ["overdue rr"],
        "IRPQ Attestation": ["irpq attestation", "irpq"],
        "Doc deficiency": ["doc deficiency"],
        # add your more categories/keywords here...
    },
    "Blocked for Transfer Transactions": {
        "Initial funding": ["initial funding"],
        "Overdue RR": ["overdue rr"],
        "Expired document": ["expired document"],
        "Block from 3pp": ["3pp", "3rd party", "third party"],
        # add more...
    },
    # add other remark types if you categorize them
}

# -----------------------
# 6) Categorize: for each account (in agg_cat) check ALL keywords for every remark present
#    - if Notes is empty -> "<Remark> - Blank"
#    - if no keyword matched but Notes exist -> "<Remark> - Uncategorized"
# -----------------------
def categories_for_account(row):
    reason_text = str(row["Notes"]).lower().strip()
    matches = []
    for remark in row["Remark"]:
        if remark not in keyword_map:
            # skip remarks with no keyword mapping
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

    # dedupe while preserving order
    seen = set()
    out = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out

agg_cat["Categories"] = agg_cat.apply(categories_for_account, axis=1)

# -----------------------
# 7) Explode to account x category rows (this is the exact input to the pivot)
# -----------------------
exploded = agg_cat.explode("Categories").copy()
exploded = exploded.dropna(subset=["Categories"])  # remove accounts with no categories (if any)
exploded = exploded.rename(columns={"Categories": "Category"})
# Keep relevant columns for verification & output
exploded = exploded[["Account", "RemarkCombo", "Category", "Notes"]].reset_index(drop=True)

# -----------------------
# 8) Pivot: rows=Category, cols=RemarkCombo, values=unique Account counts (categorised only)
# -----------------------
pivot = exploded.pivot_table(
    index="Category",
    columns="RemarkCombo",
    values="Account",
    aggfunc=lambda x: x.nunique(),
    fill_value=0
)
pivot["Total"] = pivot.sum(axis=1)  # total reasons (unique-account level) across combos

# -----------------------
# 9) Remark combo distribution (on unique-account level) — includes excluded accounts
# -----------------------
remark_combo_dist = (
    agg["RemarkCombo"]
    .value_counts()
    .reset_index()
    .rename(columns={"index": "RemarkCombo", "RemarkCombo": "Unique_Account_Count"})
)
remark_combo_dist.columns = ["RemarkCombo", "Unique_Account_Count"]
remark_combo_dist["Pct_of_Total"] = ((remark_combo_dist["Unique_Account_Count"] / agg.shape[0]) * 100).round(2)

# -----------------------
# 10) Summary values (for printing as sentences)
# -----------------------
total_unique_accounts = int(agg["Account"].nunique())
total_reasons = int(pivot["Total"].sum())   # grand total of pivot (categorised reasons count)

# -----------------------
# 11) Prepare Excel export
# -----------------------
out_filename = "remark_combinations_output.xlsx"

def autofit_columns(writer, df, sheet_name):
    worksheet = writer.sheets[sheet_name]
    for idx, col in enumerate(df.columns):
        try:
            series = df[col].astype(str)
            max_len = max(series.map(len).max(), len(str(col)))
        except Exception:
            max_len = len(str(col))
        worksheet.set_column(idx, idx, max_len + 2)

# Build the full list of combos (we will create one sheet per combo)
all_combos = agg["RemarkCombo"].unique().tolist()

# Create mapping list for Combo_Index (we'll populate counts below)
combo_map = []

with pd.ExcelWriter(out_filename, engine="xlsxwriter") as writer:
    # Write pivot
    pivot.to_excel(writer, sheet_name="Pivot_Overview", startrow=0)
    workbook = writer.book
    worksheet = writer.sheets["Pivot_Overview"]
    worksheet.freeze_panes(1, 0)

    # calculate where to write the summary lines (two blank rows per requirement)
    nrows_pivot = pivot.shape[0] + 1  # +1 for header row
    insert_row = nrows_pivot + 2

    # Write summary sentences (sentence followed by number)
    worksheet.write(insert_row, 0, "Total unique accounts:")
    worksheet.write(insert_row, 1, total_unique_accounts)

    worksheet.write(insert_row + 1, 0, "Total reasons for blocked accounts (grand total of pivot):")
    worksheet.write(insert_row + 1, 1, total_reasons)

    # Exclusion sentences (two lines below previous)
    worksheet.write(insert_row + 3, 0, "Dormant accounts excluded from categorization:")
    worksheet.write(insert_row + 3, 1, dormant_count)

    worksheet.write(insert_row + 4, 0, "Unclaimed accounts ([UC]) excluded from categorization:")
    worksheet.write(insert_row + 4, 1, uc_count)

    worksheet.write(insert_row + 5, 0, "DLA accounts excluded from categorization:")
    worksheet.write(insert_row + 5, 1, dla_count)

    # Write remark combo distribution below the above lines (leave one blank line)
    dist_start = insert_row + 7
    remark_combo_dist.to_excel(writer, sheet_name="Pivot_Overview", startrow=dist_start, index=False)

    # Autofit pivot and distribution (use reset_index for pivot to include Category column)
    autofit_columns(writer, pivot.reset_index(), "Pivot_Overview")
    autofit_columns(writer, remark_combo_dist, "Pivot_Overview")

    # Write aggregated account-level sheet (all accounts)
    agg.to_excel(writer, sheet_name="Account_Aggregated", index=False)
    autofit_columns(writer, agg, "Account_Aggregated")
    writer.sheets["Account_Aggregated"].freeze_panes(1, 0)

    # Write exploded account-category sheet (this is EXACTLY what pivot is derived from)
    exploded.to_excel(writer, sheet_name="Account_Category", index=False)
    autofit_columns(writer, exploded, "Account_Category")
    writer.sheets["Account_Category"].freeze_panes(1, 0)

    # For each combo, create a sheet with both categorized rows and excluded rows, with a flag
    for i, combo in enumerate(all_combos, start=1):
        sheet_name = f"Combo_{i}"
        # categorized rows for this combo (from exploded)
        expl_subset = exploded[exploded["RemarkCombo"] == combo].copy()
        if not expl_subset.empty:
            expl_subset["IncludedForCategorization"] = True
        else:
            expl_subset = pd.DataFrame(columns=["Account", "RemarkCombo", "Category", "Notes", "IncludedForCategorization"])

        # excluded rows for this combo (from agg where mask_exclude True)
        excl_subset = agg[(agg["RemarkCombo"] == combo) & mask_exclude].copy()
        if not excl_subset.empty:
            # create the same columns as expl_subset for compatibility
            excl_subset = excl_subset[["Account", "RemarkCombo", "Notes", "is_dormant", "is_uc", "is_dla"]].copy()
            excl_subset["Category"] = ""  # no category since excluded
            excl_subset["IncludedForCategorization"] = False
            # reorder to match expl_subset
            excl_subset = excl_subset[["Account", "RemarkCombo", "Category", "Notes", "IncludedForCategorization", "is_dormant", "is_uc", "is_dla"]]
        else:
            excl_subset = pd.DataFrame(columns=["Account", "RemarkCombo", "Category", "Notes", "IncludedForCategorization", "is_dormant", "is_uc", "is_dla"])

        # bring expl_subset into the same column layout and add flags columns (from agg)
        if not expl_subset.empty:
            # merge flags from agg for these accounts
            flags = agg.set_index("Account")[["is_dormant", "is_uc", "is_dla"]]
            expl_subset = expl_subset.merge(flags, left_on="Account", right_index=True, how="left")
            # ensure column order
            expl_subset = expl_subset[["Account", "RemarkCombo", "Category", "Notes", "IncludedForCategorization", "is_dormant", "is_uc", "is_dla"]]

        # combine categorized and excluded rows so user can reconcile in one sheet
        combo_sheet_df = pd.concat([expl_subset, excl_subset], ignore_index=True, sort=False).fillna({"is_dormant": False, "is_uc": False, "is_dla": False})

        # write to sheet
        combo_sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        autofit_columns(writer, combo_sheet_df, sheet_name)
        writer.sheets[sheet_name].freeze_panes(1, 0)

        # mapping info for Combo_Index
        combo_map.append({
            "Combo_Sheet": sheet_name,
            "RemarkCombo": combo,
            "Unique_Accounts_All": int(agg.loc[agg["RemarkCombo"] == combo, "Account"].nunique()),
            "Unique_Accounts_IncludedForCategorization": int(exploded.loc[exploded["RemarkCombo"] == combo, "Account"].nunique()),
            "Unique_Accounts_Excluded": int(agg.loc[(agg["RemarkCombo"] == combo) & mask_exclude, "Account"].nunique())
        })

    # Write Combo_Index
    combo_df = pd.DataFrame(combo_map)
    combo_df.to_excel(writer, sheet_name="Combo_Index", index=False)
    autofit_columns(writer, combo_df, "Combo_Index")
    writer.sheets["Combo_Index"].freeze_panes(1, 0)

print(f"Saved file: {out_filename}")
print("Total unique accounts:", total_unique_accounts)
print("Total reasons (grand total of pivot):", total_reasons)
print("Dormant excluded:", dormant_count)
print("Unclaimed [UC] excluded:", uc_count)
print("DLA excluded:", dla_count)