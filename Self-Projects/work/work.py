import pandas as pd

# Sample data
data = {
    'RM Name': ['RM1', 'RM1', 'RM2', 'RM2', 'RM3', 'RM3', 'RM1', 'RM1'],
    'Cash': [100, 0, 0, 0, 0, 200, 0, 100],
    'Deposit': [0, 200, 0, 0, 0, 0, 0, 0],
    'Share Bond': [0, 0, 300, 0, 0, 0, 0, 0],
    'Struct. Prod.': [0, 0, 0, 400, 0, 0, 0, 0],
    'Derivatives': [0, 0, 0, 0, 500, 0, 0, 0],
    'Fund': [0, 0, 0, 0, 0, 0, 0, 0],
    'Other': [0, 0, 0, 0, 0, 0, 0, 0],
    'Loan': [0, 0, 0, 0, 0, 0, 0, 0],
    'BPKey': ['C1', 'C1', 'C2', 'C2', 'C3', 'C3', 'C4', 'C4'],
    'Total_FEE': [0, 0, 100, 0, 0, 0, 0, 100]
}

# Create DataFrame
df = pd.DataFrame(data)

# List of investment categories
investment_columns = ['Cash', 'Deposit', 'Share Bond', 'Struct. Prod.', 'Derivatives', 'Fund', 'Other', 'Loan']

# Group by BPKey and aggregate
grouped = df.groupby('BPKey').agg({
    'RM Name': 'first',                              # Take the RM Name (assumes it's the same for all rows of a BPKey)
    'Total_FEE': lambda x: (x == 0).all(),          # Check if fee is waived for all months
    **{col: 'sum' for col in investment_columns}    # Sum investments for each category
}).reset_index()

# Identify exclusive investments
grouped['exclusive_category'] = grouped[investment_columns].apply(
    lambda row: row.idxmax() if (row > 0).sum() == 1 else None, axis=1
)

# Filter clients with waived fees and exclusive investments
exclusive_waived_clients = grouped[grouped['Total_FEE'] & grouped['exclusive_category'].notna()]

# Group by RM Name and exclusive category to count unique clients
result = exclusive_waived_clients.groupby(['RM Name', 'exclusive_category'])['BPKey'].nunique().reset_index(name='unique_client_count')

# Output results
print(result)
