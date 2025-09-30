import pandas as pd
from matplotlib import pyplot as plt
from matplotlib_venn import venn2

# Assuming df is already cleaned and has columns: Account, Remark

# Step 1: Create flags for each remark type per account
account_flags = df.groupby("Account")["Remark"].apply(list).reset_index()

def get_flags(remark_list):
    return pd.Series({
        "Total_Block_Flag": int(any("Total Blocking" in r for r in remark_list)),
        "Transfer_Block_Flag": int(any("Blocked for Transfer Transactions" in r for r in remark_list))
    })

account_flags = account_flags.join(account_flags["Remark"].apply(get_flags))

# Step 2: Count numbers for Venn diagram
total_only = ((account_flags["Total_Block_Flag"] == 1) & (account_flags["Transfer_Block_Flag"] == 0)).sum()
transfer_only = ((account_flags["Total_Block_Flag"] == 0) & (account_flags["Transfer_Block_Flag"] == 1)).sum()
both = ((account_flags["Total_Block_Flag"] == 1) & (account_flags["Transfer_Block_Flag"] == 1)).sum()

# Step 3: Plot Venn diagram
plt.figure(figsize=(6,6))
venn2(subsets=(total_only, transfer_only, both),
      set_labels=("Total Block", "Transfer Block"))
plt.title("Accounts with Total / Transfer Blocks")
plt.show()