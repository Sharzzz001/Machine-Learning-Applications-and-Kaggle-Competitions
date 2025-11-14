
# Create a numeric version of the duration column
df["Age_num"] = df["Age"].str.extract(r'(\d+)').astype(int)

# Separate rows with "Yes (multiple)"
multiple_df = df[df["Matched"] == "Yes (multiple)"].copy()

# Sort so highest age stays
multiple_df = multiple_df.sort_values(by="Age_num", ascending=False)

# Drop duplicates based on identifying columns, keep the one with highest age
multiple_df = multiple_df.drop_duplicates(subset=["AccountNumber", "RequestType", "DocName"], keep="first")

# Rows not affected (everything except Yes (multiple))
other_df = df[df["Matched"] != "Yes (multiple)"]

# Combine back
result = pd.concat([other_df, multiple_df]).sort_index()

# Optional: remove helper column
result = result.drop(columns=["Age_num"])

