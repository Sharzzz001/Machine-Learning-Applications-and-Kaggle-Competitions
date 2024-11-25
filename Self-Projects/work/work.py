import pandas as pd

# Assuming your DataFrame is named `aum_df`
# Columns: ['BP Key', 'Month', 'AUM', 'RM', 'Cash', 'Deposit', 'Share Bond', 'Struct. Prod.', 'Derivatives', 'Fund', 'Other']

# Group by RM and calculate required metrics
summary_df = (
    aum_df.groupby('RM')
    .agg(
        total_clients=('BP Key', 'nunique'),       # Count of unique clients per RM
        total_aum=('AUM', 'sum'),                 # Total AUM per RM
        total_cash=('Cash', 'sum'),               # Total Cash per RM
        total_deposit=('Deposit', 'sum'),         # Total Deposit per RM
        total_share_bond=('Share Bond', 'sum'),   # Total Share Bond per RM
        total_struct_prod=('Struct. Prod.', 'sum'),# Total Structured Products per RM
        total_derivatives=('Derivatives', 'sum'), # Total Derivatives per RM
        total_fund=('Fund', 'sum'),               # Total Fund per RM
        total_other=('Other', 'sum')              # Total Other per RM
    )
    .reset_index()
)

# Calculate percentage contributions for each component
component_columns = [
    'total_cash', 'total_deposit', 'total_share_bond', 
    'total_struct_prod', 'total_derivatives', 'total_fund', 'total_other'
]

for col in component_columns:
    summary_df[f'{col}_pct'] = (summary_df[col] / summary_df['total_aum']) * 100

# Final Summary DataFrame
print(summary_df)
