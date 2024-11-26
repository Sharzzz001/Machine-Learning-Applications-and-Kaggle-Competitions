import pandas as pd

# Sample data
data = {
    'RM Name': ['RM1', 'RM1', 'RM2', 'RM2', 'RM3', 'RM3'],
    'Cash': [100, 0, 0, 0, 0, 200],
    'Deposit': [0, 200, 0, 0, 0, 0],
    'Share Bond': [0, 0, 300, 0, 0, 0],
    'Struct. Prod.': [0, 0, 0, 400, 0, 0],
    'Derivatives': [0, 0, 0, 0, 500, 0],
    'Fund': [0, 0, 0, 0, 0, 0],
    'Other': [0, 0, 0, 0, 0, 0],
    'Loan': [0, 0, 0, 0, 0, 0],
    'BPKey': ['C1', 'C2', 'C3', 'C4', 'C5', 'C6'],
    'Total_FEE': [0, 0, 100, 0, 0, 0]
}

# Create DataFrame
df = pd.DataFrame(data)

# List of investment categories
investment_columns = ['Cash', 'Deposit', 'Share Bond', 'Struct. Prod.', 'Derivatives', 'Fund', 'Other', 'Loan']

# Identify clients with waived fees
waived_clients = df[df['Total_FEE'] == 0].copy()

# Check exclusive investments
waived_clients['exclusive_category'] = waived_clients[investment_columns].apply(
    lambda row: row.idxmax() if (row > 0).sum() == 1 else None, axis=1
)

# Filter clients who invest exclusively in one category
exclusive_waived_clients = waived_clients.dropna(subset=['exclusive_category'])

# Group by RM Name and exclusive category to count
result = exclusive_waived_clients.groupby(['RM Name', 'exclusive_category']).size().reset_index(name='count')

# Output results
print(result)
