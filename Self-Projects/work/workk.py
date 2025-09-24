import pandas as pd

# Example dataframe
data = {
    "Remark": [
        "Total Block", "Total Block", "Transfer Block", 
        "Transfer Block", "Total Block", "Transfer Block"
    ],
    "Note Block BP Status": [
        "Overdue RR - client not responding",
        "AI Proof missing",
        "Initial funding not received",
        "Some random reason",
        "Irpq attestation pending",
        "CAC not submitted"
    ]
}

df = pd.DataFrame(data)

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

# Function to assign category
def categorize(row):
    remark = row["Remark"]
    text = str(row["Note Block BP Status"]).lower()

    for category, keywords in keyword_map.get(remark, {}).items():
        for kw in keywords:
            if kw in text:
                return f"{remark} - {category}"
    return f"{remark} - Uncategorized"

df["Category"] = df.apply(categorize, axis=1)

# Get counts
counts = df["Category"].value_counts()

print(df)
print("\nCounts:\n", counts)