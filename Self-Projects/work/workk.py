import pandas as pd
import numpy as np

# Example keyword map
keyword_map = {
    "Total Block": {
        "Court": "Court Related",
        "Arrest": "Law Enforcement",
    },
    "Transfer Block": {
        "KYC": "KYC Issue",
        "Limit": "Limit Breach",
    }
}

# --- Function to categorize ---
def categorize(row, keyword_map):
    remark = row["Remark"]
    note = row["Note block BP Status"]

    # Handle NaN separately
    if pd.isna(note):
        if remark == "Total Block":
            return "Total Block - Blank"
        elif remark == "Transfer Block":
            return "Transfer Block - Blank"
        else:
            return "Uncategorised"

    if remark in keyword_map:
        for kw, cat in keyword_map[remark].items():
            if kw.lower() in note.lower():
                return cat

    return "Uncategorised"


# --- Data Prep ---
# Clean up Dormant variations
df["Remark"] = df["Remark"].str.replace(r"Dormant since.*", "Dormant", regex=True)

# Categorize
df["Category"] = df.apply(lambda x: categorize(x, keyword_map), axis=1)

# Remark combinations per account
remark_combos = (
    df.groupby("Account Name")["Remark"]
    .apply(lambda x: " + ".join(sorted(set(x))))
    .reset_index()
)

# Merge back Note block for keyword scan
merged = df.merge(remark_combos, on="Account Name", suffixes=("", "_combo"))

# --- Pivot for overview ---
pivot = pd.pivot_table(
    merged,
    index="Remark_combo",
    columns="Category",
    values="Account Name",
    aggfunc=lambda x: len(set(x)),
    fill_value=0
)

print(pivot)

# --- Export to Excel ---
with pd.ExcelWriter("remark_combinations_output.xlsx", engine="xlsxwriter") as writer:
    # Write pivot overview
    pivot.to_excel(writer, sheet_name="Pivot_Overview")

    # Write each combination separately
    for combo in merged["Remark_combo"].unique():
        subset = merged[merged["Remark_combo"] == combo]
        subset.to_excel(writer, sheet_name=combo[:31], index=False)  # sheet name limit = 31 chars