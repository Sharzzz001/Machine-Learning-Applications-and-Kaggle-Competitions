import pandas as pd

# Example input
# df has: Account, Remark, Note Block BP Status

# Step 1: normalize remarks (replace "Dormant since <date>" → "Dormant", etc.)
df["Remark"] = df["Remark"].str.replace(r"Dormant.*", "Dormant", regex=True)

# Step 2: collapse remarks per account into a sorted combination
remark_combos = df.groupby("Account")["Remark"].apply(lambda x: tuple(sorted(set(x)))).reset_index()
remark_combos["RemarkCombo"] = remark_combos["Remark"].apply(lambda x: " + ".join(x))

# Step 3: build keyword map (simplified example from your structure)
keyword_map = {
    "Total Block": {
        "Overdue RR": ["overdue rr"],
        "IRPQ Attestation": ["irpq attestation", "irpq"],
        "Blanks": [""]
    },
    "Transfer Block": {
        "Initial funding": ["initial funding"],
        "Expired document": ["expired document"],
        "Blanks": [""]
    }
    # add other remark types...
}

# Step 4: explode matches (check all keywords, don’t stop at first)
def categorize_all(row):
    remark_texts = row["Remark"]
    reason_text = str(df.loc[df["Account"] == row["Account"], "Note Block BP Status"].tolist()).lower()
    matches = []
    for remark in remark_texts:
        if remark in keyword_map:
            for category, keywords in keyword_map[remark].items():
                if any(kw in reason_text for kw in keywords if kw):  # non-blank keywords
                    matches.append(f"{remark} - {category}")
            # handle blanks
            if not any(kw in reason_text for kws in keyword_map[remark].values() for kw in kws if kw):
                matches.append(f"{remark} - Blanks")
    return list(set(matches))  # unique categories per account

remark_combos["Categories"] = remark_combos.apply(categorize_all, axis=1)

# Step 5: explode into account × category
exploded = remark_combos.explode("Categories")

# Step 6: build pivot
pivot = exploded.pivot_table(
    index="Categories",
    columns="RemarkCombo",
    values="Account",
    aggfunc=lambda x: x.nunique(),
    fill_value=0
)

print(pivot)