import pandas as pd

# Example assumption: your main file is df_main
# df_main has columns: AccountNumber, RequestType

# Split into AO vs others
df_main_ao = df_main[df_main['RequestType'].str.upper() == 'ACCOUNT OPENING']
df_main_rr = df_main[df_main['RequestType'].str.upper() != 'ACCOUNT OPENING']

# Merge AO records with df_ao
df_main_ao = df_main_ao.merge(
    df_ao,
    how='left',
    left_on='AccountNumber',
    right_on='AccountNumber'
)

# Merge RR/other records with df_rr
df_main_rr = df_main_rr.merge(
    df_rr,
    how='left',
    left_on='AccountNumber',
    right_on='AccountNumber'
)

# Combine back together
df_with_sales = pd.concat([df_main_ao, df_main_rr], ignore_index=True)

# Now merge with scm_df to get RM Name
df_final = df_with_sales.merge(
    scm_df,
    how='left',
    on='Sales Code'   # assumes column is named exactly "Sales Code"
)

# df_final now has: AccountNumber, RequestType, Sales Code, RM