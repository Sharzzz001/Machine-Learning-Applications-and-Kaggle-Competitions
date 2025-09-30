import pandas as pd
from upsetplot import UpSet, from_indicators
from matplotlib import pyplot as plt

# === Assume df has columns: Account, Remark ===

# Step 1: Deduplicate account × remark
df_unique = df.drop_duplicates(subset=["Account", "Remark"])

# Step 2: Get list of block types dynamically
block_types = df_unique["Remark"].unique().tolist()

# Step 3: Create binary presence table per account
account_flags = df_unique.groupby("Account")["Remark"].apply(list).reset_index()
for b in block_types:
    account_flags[b] = account_flags["Remark"].apply(lambda x: int(b in x))

# Step 4: Create UpSet data
indicator_df = account_flags.set_index("Account")[block_types]
upset_data = from_indicators(indicator_df.columns, indicator_df)

# Step 5: Plot UpSet
upset = UpSet(upset_data, subset_size='count', show_counts='%d')
upset.plot()
plt.title("Overlap of Block Types Across Accounts")
plt.show()