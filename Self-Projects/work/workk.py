import pandas as pd
from typing import List

# -------------------------
# INPUT: your dataframe `df`
# Columns expected: "Account", "Remark", "Note Block BP Status"
# Example: df = pd.read_excel("active_test.xlsx", sheet_name="Cleaned_Data")
# -------------------------

# --- 1) Normalise remarks (so different phrasings like "Dormant since ..." become "Dormant") ---
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
    return s  # keep original otherwise

df["Remark"] = df["Remark"].apply(normalize_remark)

# --- 2) Example keyword_map (replace/extend with your full map) ---
# Keys must match the normalized Remark values used above.
keyword_map = {
    "Total Blocking": {
        "Overdue RR": ["overdue rr"],
        "IRPQ Attestation": ["irpq attestation", "irpq"],
        "AI Proof / AI supp doc": ["ai proof", "ai supp doc", "ai documentary proof"],
        "DA": ["dia"],
        "Doc deficiency": ["doc deficiency"],
        "Physical document": ["physical document"],
        "Deceased": ["deceased", "death", "demise"],
        "Unclaimed": ["unclaimed"],
        "Bankruptcy": ["bankruptcy", "chap 11"],
        "CAC": ["cac"]
    },
    "Blocked for Transfer Transactions": {
        "Initial funding": ["initial funding"],
        "Overdue RR": ["overdue rr"],
        "Expired document": ["expired document"],
        "CAC": ["cac"],
        "Restrict to 1pp": ["restrict to 1pp", "1st party payment", "1st party", "first party"],
        "Block from 3pp": ["3pp", "3rd party transfer", "3d party txn", "3rd party", "third party"]
    },
    # Add other remark types & categories as needed...
}

# -------------------------
# 3) Aggregate data per Account:
#    - Remark list (unique, sorted)
#    - Concatenate all Note Block texts (unique non-empty)
# -------------------------
def combine_notes(series: pd.Series) -> str:
    # keep unique non-empty note texts, join with delimiter
    texts = [str(x).strip() for x in series.dropna().astype(str)]
    texts = [t for t in texts if t]  # remove empty strings
    # dedupe while preserving order
    seen = set()
    out = []
    for t in texts:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return " || ".join(out)

agg = (
    df
    .groupby("Account", sort=False)
    .agg({
        "Remark": lambda x: sorted(set(x.dropna().astype(str))),
        "Note Block BP Status": combine_notes
    })
    .reset_index()
    .rename(columns={"Note Block BP Status": "Notes"})
)

# Create a human-friendly combo string (order-invariant)
agg["RemarkCombo"] = agg["Remark"].apply(lambda lst: " + ".join(lst) if lst else "(No Remark)")

# -------------------------
# 4) For each account, check ALL relevant keywords (do NOT stop at first match).
#    Produce a list of matched categories like "Total Blocking - Overdue RR"
#    Also handle Blanks and Uncategorized per remark.
# -------------------------
def categories_for_account(row) -> List[str]:
    reason_text = str(row["Notes"]).lower().strip()
    categories = []
    # if no remarks present, return none
    if not row["Remark"]:
        return []
    for remark in row["Remark"]:
        # skip remarks we have no keyword map for
        if remark not in keyword_map:
            # if you still want to record Uncategorized for unknown remarks, uncomment:
            # categories.append(f"{remark} - Uncategorized")
            continue

        found_any = False
        for cat_name, kw_list in keyword_map[remark].items():
            for kw in kw_list:
                if not kw:
                    continue
                if kw.lower() in reason_text:
                    categories.append(f"{remark} - {cat_name}")
                    found_any = True
                    break  # stop checking other keywords inside this category (but continue other categories)
        # after checking all categories for this remark
        if not found_any:
            # if the aggregated notes are empty -> Blanks, else Uncategorized
            if reason_text == "":
                categories.append(f"{remark} - Blanks")
            else:
                categories.append(f"{remark} - Uncategorized")

    # make unique and preserve order
    seen = set()
    out = []
    for c in categories:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out

agg["Categories"] = agg.apply(categories_for_account, axis=1)

# -------------------------
# 5) Explode to account x category rows, then pivot: rows=Category, cols=RemarkCombo, values=unique account counts
# -------------------------
exploded = agg.explode("Categories")
# drop accounts that had no matching categories (Categories = NaN)
exploded = exploded.dropna(subset=["Categories"]).copy()

pivot = exploded.pivot_table(
    index="Categories",
    columns="RemarkCombo",
    values="Account",
    aggfunc=lambda x: x.nunique(),   # count unique accounts per (category, combo)
    fill_value=0
)

# Optional: add an overall total column (number of unique accounts matching each category across all combos)
pivot["Total"] = pivot.sum(axis=1)

# Optional: ensure all 9 predefined combos appear as columns (if you have a canonical list):
# predefined_combos = ["Total Blocking", "Blocked for Transfer Transactions", "Dormant", "...", "..."]
# pivot = pivot.reindex(columns=[*predefined_combos, "Total"], fill_value=0)

# -------------------------
# 6) Output
# -------------------------
print("Total unique accounts (rows in agg):", agg.shape[0])
print("\nPivot (Categories x RemarkCombo) — top rows:")
print(pivot.head(40))

# You can save to excel:
pivot.to_excel("category_by_remarkcombo_pivot.xlsx")
print("\nSaved pivot to category_by_remarkcombo_pivot.xlsx")