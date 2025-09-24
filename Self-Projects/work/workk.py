import pandas as pd

# Example dataframe
data = {
    "Remark": [
        "Total Block", "Total Block - Auto", "Transfer Block",
        "Transfer Block - Manual", "Some Other Remark", "Total Block - Temp"
    ],
    "Note Block BP Status": [
        "Overdue RR - client not responding",
        "AI Proof missing",
        "Initial funding not received",
        "Some random reason",
        "Not relevant",
        "Irpq attestation pending"
    ]
}

df = pd.DataFrame(data)

# 🔹 Filter only rows with Total Block / Transfer Block
df = df[df["Remark"].str.contains("Total Block|Transfer Block", case=False, na=False)].copy()

# Define keyword dictionaries
keyword_map = {
    "Total Block": {
        "Overdue RR": ["overdue rr"],
        "Irpq attestation": ["irpq attestation"],
        "AI Proof / AI supp doc": ["ai proof", "ai supp doc"]
    },
    "Transfer Block": {
        "Initial funding": ["initial funding"],
        "Overdue RR": ["overdue rr"],
        "CAC": ["cac"]
    }
}

# Function to assign keyword category properly
def categorize(row):
    remark_text = row["Remark"].lower()
    reason_text = str(row["Note Block BP Status"]).lower()

    # Identify which remark type
    if "total block" in remark_text:
        remark_type = "Total Block"
    elif "transfer block" in remark_text:
        remark_type = "Transfer Block"
    else:
        return "Other"

    # Check against keywords for that type
    for category, keywords in keyword_map[remark_type].items():
        for kw in keywords:
            if kw in reason_text:
                return f"{remark_type} - {category}"

    return f"{remark_type} - Uncategorized"

# Apply categorization
df["Category"] = df.apply(categorize, axis=1)

# Summary table
summary = df["Category"].value_counts().reset_index()
summary.columns = ["Category", "Count"]

print(df)
print("\nSummary:\n", summary)