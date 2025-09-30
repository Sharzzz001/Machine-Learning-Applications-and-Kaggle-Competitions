import pandas as pd

# === Load data ===
df = pd.read_excel("active_test.xlsx", sheet_name="Cleaned_Data")

# Filter only the relevant remark rows
df = df[df["Remark"].str.contains("Total Blocking|Blocked for Transfer Transactions",
                                  case=False, na=False)].copy()

# Ensure Account column exists (assuming it's called "Account Name")
df.rename(columns={"Account Name": "Account"}, inplace=True)

# === 1. Total unique accounts blocked ===
total_unique_accounts = df["Account"].nunique()
print("Total unique accounts blocked:", total_unique_accounts)

# === 2. Individual remark counts (unique accounts per remark) ===
individual_counts = (
    df.groupby("Remark")["Account"].nunique().reset_index(name="Unique_Accounts")
)
print("\nIndividual remark counts:")
print(individual_counts)

# === 3. Group remark combinations ===
account_remarks = (
    df.groupby("Account")["Remark"]
      .apply(lambda x: sorted(set(x.str.lower())))  # normalize + sort
      .reset_index(name="Remark_List")
)

# Join remarks into a single string so order doesn’t matter
account_remarks["Remark_Combination"] = account_remarks["Remark_List"].apply(
    lambda x: ", ".join(x)
)

combination_counts = (
    account_remarks["Remark_Combination"].value_counts().reset_index()
)
combination_counts.columns = ["Remark_Combination", "Account_Count"]

print("\nRemark combination counts:")
print(combination_counts)

# === 4. Special condition: Unclaimed accounts ===
unclaimed_accounts = df[df["Account"].str.contains(r"\[UC\]", case=False, na=False)]["Account"].nunique()
print("\nUnclaimed unique accounts (with [UC]):", unclaimed_accounts)