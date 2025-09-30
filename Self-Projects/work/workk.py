import pandas as pd
import re

# -----------------------
# LOAD your data into `df`
# Example:
# df = pd.read_excel("active_test.xlsx", sheet_name="Cleaned_Data")
# -----------------------
# For safety, work on a copy:
df = df.copy()

# --- 0) Ensure column names we expect ---
# Accept either "Account" or "Account Name"
if "Account Name" in df.columns and "Account" not in df.columns:
    df.rename(columns={"Account Name": "Account"}, inplace=True)

# Try to detect the notes column (any column with 'note' in its name)
note_cols = [c for c in df.columns if "note" in c.lower()]
if note_cols:
    note_col = note_cols[0]
else:
    # fallback; change if your actual column name differs
    note_col = "Note Block BP Status"

# --- 1) Normalize remarks (so "Dormant since <date>" doesn't create many variants) ---
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
    return s  # else keep as-is

df["Remark"] = df["Remark"].apply(normalize_remark)

# --- 2) Helper to combine / aggregate notes per account (dedupe & preserve order) ---
def combine_notes(series: pd.Series) -> str:
    texts = [str(x).strip() for x in series.dropna().astype(str)]
    texts = [t for t in texts if t]  # remove empty
    seen = set()
    out = []
    for t in texts:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return " || ".join(out)

# --- 3) Aggregate per account: list of unique remarks + combined notes ---
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

# Create a stable, order-invariant combo string for pivot columns
agg["RemarkCombo"] = agg["Remark"].apply(lambda lst: " + ".join(lst) if lst else "(No Remark)")

# -----------------------
# 4) Define your keyword_map (replace with your full map). Keys must match normalized Remark values.
# Example structure:
keyword_map = {
    "Total Blocking": {
        "Overdue RR": ["overdue rr"],
        "IRPQ Attestation": ["irpq attestation", "irpq"],
        "Doc deficiency": ["doc deficiency"],
        # ... add all categories/keywords for Total Blocking
    },
    "Blocked for Transfer Transactions": {
        "Initial funding": ["initial funding"],
        "Expired document": ["expired document"],
        "Block from 3pp": ["3pp", "3rd party", "third party"],
        # ... add all categories/keywords for Transfer
    },
    # add other remark types if you want categories for them
}
# -----------------------

# --- 5) For each account, check ALL keywords for each remark present (do not stop at first match).
def categories_for_account(row):
    reason_text = str(row["Notes"]).lower().strip()
    matches = []

    # iterate each remark present on the account
    for remark in row["Remark"]:
        # if we don't have keywords defined for this remark, skip or optionally tag Uncategorized
        if remark not in keyword_map:
            # optionally: matches.append(f"{remark} - Uncategorized")
            continue

        if reason_text == "":  # aggregated notes empty -> label Blank for this remark
            matches.append(f"{remark} - Blank")
            continue

        found_for_remark = False
        # check every category for this remark; if any keyword of the category matches, add the category
        for cat_name, kw_list in keyword_map[remark].items():
            for kw in kw_list:
                if kw and kw.lower() in reason_text:
                    matches.append(f"{remark} - {cat_name}")
                    found_for_remark = True
                    break  # stop checking other keywords for this category (but continue other categories)
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

agg["Categories"] = agg.apply(categories_for_account, axis=1)

# --- 6) Explode into account x category rows (so one account appears once per matched category) ---
exploded = agg.explode("Categories").copy()
exploded = exploded.dropna(subset=["Categories"])  # accounts without any category are removed

# --- 7) Pivot: rows=Categories, cols=RemarkCombo, values=unique Account counts ---
pivot = exploded.pivot_table(
    index="Categories",
    columns="RemarkCombo",
    values="Account",
    aggfunc=lambda x: x.nunique(),
    fill_value=0
)

# Add a 'Total' column (total unique accounts matching each category across all combos)
pivot["Total"] = pivot.sum(axis=1)

# --- 8) Save pivot + one sheet per remark combo (sheet names sanitized & truncated) ---
out_filename = "remark_combinations_output.xlsx"

def sanitize_sheetname(name: str) -> str:
    # remove characters Excel forbids in sheet names and trim to 31 chars
    name = re.sub(r'[:\\/*?\[\]]', "_", name)
    return name[:31]

with pd.ExcelWriter(out_filename) as writer:
    pivot.to_excel(writer, sheet_name="Pivot_Overview")
    # write aggregated account-level (agg) for reference
    agg.to_excel(writer, sheet_name="Account_Aggregated", index=False)
    # write each remark combo's detailed raw rows (from original df) into its own sheet
    combos = agg["RemarkCombo"].unique()
    for combo in combos:
        sheet = sanitize_sheetname(combo)
        accounts_in_combo = agg.loc[agg["RemarkCombo"] == combo, "Account"].tolist()
        subset_rows = df[df["Account"].isin(accounts_in_combo)].copy()
        # write original rows for those accounts (you can change columns if you prefer agg rows instead)
        subset_rows.to_excel(writer, sheet_name=sheet, index=False)

print(f"Saved pivot and combination sheets to '{out_filename}'")
print("Total unique accounts:", agg.shape[0])
print("Pivot shape (categories x combos):", pivot.shape)