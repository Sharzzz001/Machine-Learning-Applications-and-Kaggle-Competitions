import pandas as pd

# 1️⃣ RR join to AOB on account_number
merged = pd.merge(AOB, RR, on='account_number', how='left', suffixes=('_aob', '_rr'))

# 2️⃣ SCM join to AOB on salescode ↔ title
merged = pd.merge(merged, SCM, left_on='salescode', right_on='title', how='left')

# 3️⃣ COB join to AOB on assigner_toid ↔ login_nameid
merged = pd.merge(merged, COB, left_on='assigner_toid', right_on='login_nameid', how='left', suffixes=('', '_cob'))

final_df = merged[[
    'account_number_rr',   # From RR
    'account_name',        # From AOB (assuming column exists)
    'RM_name',             # From SCM
    'Title'                # From COB (this is the Title of assigner_toid)
]]