import pandas as pd
import re

# -------------------------
# Load your data
# -------------------------
# df = pd.read_excel("active_test.xlsx", sheet_name="Cleaned_Data")
df = df.copy()  # assume df exists in memory

# -------------------------
# Detect/normalize columns
# -------------------------
if "Account Name" in df.columns and "Account" not in df.columns:
    df.rename(columns={"Account Name": "Account"}, inplace=True)
if "Account subtitle" not in df.columns:
    df["Account subtitle"] = ""  # fallback if column not present

note_cols = [c for c in df.columns if "note" in c.lower()]
note_col = note_cols[0] if note_cols else "Note Block BP Status"

# -------------------------
# Normalize remarks
# -------------------------
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

# -------------------------
# Keyword map (shortened example)
# -------------------------
keyword_map = {
    "Total Blocking": {
        "Overdue RR": ["overdue rr"],
        "IRPQ Attestation": ["irpq attestation", "irpq"],
        "Doc deficiency": ["doc deficiency"],
    },
    "Blocked for Transfer Transactions": {
        "Initial funding": ["initial funding"],
        "Expired document": ["expired document"],
        "Block from 3pp": ["3pp", "3rd party", "third party"],
    },
}

# -------------------------
# Combine notes per account
# -------------------------
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

# -------------------------
# Aggregate per account
# -------------------------
agg = (
    df
    .groupby(["Account", "Account subtitle"], sort=False)
    .agg({
        "Remark": lambda x: sorted(set(x.dropna().astype(str))),
        note_col: combine_notes
    })
    .reset_index()
    .rename(columns={note_col: "Notes"})
)
agg["RemarkCombo"] = agg["Remark"].apply(lambda lst: " + ".join(lst) if lst else "(No Remark)")

# -------------------------
# Identify exclusions
# -------------------------
agg["is_dormant"] = agg["Remark"].apply(lambda r: any("Dormant" in str(x) for x in r))
agg["is_uc"] = agg["Account subtitle"].astype(str).str.contains(r"\[UC\]", case=False, na=False)
agg["is_dla"] = agg["Notes"].str.contains("DLA", case=False, na=False)

# Exclusion masks
mask_exclude = agg["is_dormant"] | agg["is_uc"] | agg["is_dla"]

# For reporting
dormant_count = agg.loc[agg["is_dormant"], "Account"].nunique()
uc_count = agg.loc[agg["is_uc"], "Account"].nunique()
dla_count = agg.loc[agg["is_dla"], "Account"].nunique()

# Subset to accounts eligible for categorization
agg_cat = agg.loc[~mask_exclude].copy()

# -------------------------
# Categorization
# -------------------------
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
    # dedupe
    seen, out = set(), []
    for m in matches:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out

agg_cat["Categories"] = agg_cat.apply(categories_for_account, axis=1)

# Explode
exploded = agg_cat.explode("Categories").dropna(subset=["Categories"])
exploded = exploded[["Account", "RemarkCombo", "Categories", "Notes"]].rename(columns={"Categories": "Category"})

# Pivot
pivot = exploded.pivot_table(
    index="Category",
    columns="RemarkCombo",
    values="Account",
    aggfunc=lambda x: x.nunique(),
    fill_value=0
)
pivot["Total"] = pivot.sum(axis=1)

# -------------------------
# Summary values
# -------------------------
total_unique_accounts = agg["Account"].nunique()
total_reasons = pivot["Total"].sum()

# -------------------------
# Write to Excel
# -------------------------
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

with pd.ExcelWriter(out_filename, engine="xlsxwriter") as writer:
    # Write pivot
    pivot.to_excel(writer, sheet_name="Pivot_Overview", startrow=0)
    worksheet = writer.sheets["Pivot_Overview"]
    worksheet.freeze_panes(1, 0)

    nrows_pivot = pivot.shape[0] + 1
    insert_row = nrows_pivot + 2

    # Totals and exclusions
    worksheet.write(insert_row, 0, "Total unique accounts")
    worksheet.write(insert_row, 1, total_unique_accounts)

    worksheet.write(insert_row + 1, 0, "Total reasons for blocked accounts")
    worksheet.write(insert_row + 1, 1, int(total_reasons))

    worksheet.write(insert_row + 3, 0, "Dormant accounts excluded from categorization")
    worksheet.write(insert_row + 3, 1, int(dormant_count))

    worksheet.write(insert_row + 4, 0, "Unclaimed [UC] accounts excluded from categorization")
    worksheet.write(insert_row + 4, 1, int(uc_count))

    worksheet.write(insert_row + 5, 0, "DLA accounts excluded from categorization")
    worksheet.write(insert_row + 5, 1, int(dla_count))

    # Autofit
    autofit_columns(writer, pivot.reset_index(), "Pivot_Overview")

print(f"Saved file: {out_filename}")
print("Total unique accounts:", total_unique_accounts)
print("Dormant excluded:", dormant_count)
print("Unclaimed [UC] excluded:", uc_count)
print("DLA excluded:", dla_count)