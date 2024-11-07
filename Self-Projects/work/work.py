import pandas as pd
import numpy as np

# Sample data with an additional `waived_amount` column
data = {
    'client_name': ['Client A', 'Client A', 'Client A', 'Client B', 'Client B', 'Client B', 'Client C', 'Client C', 'Client C'],
    'waived': ['Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'Yes', 'Yes', 'Yes'],
    'total_aum': [100, 105, 110, 150, 145, 155, 120, 125, 123],
    'file_name': ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Jan 2024', 'Feb 2024', 'Mar 2024', 'Jan 2024', 'Feb 2024', 'Mar 2024'],
    'waived_amount': [50, 55, 60, 0, 0, 0, 30, 35, 32]
}

df = pd.DataFrame(data)

# Convert file_name to datetime to sort by month
df['file_name'] = pd.to_datetime(df['file_name'], format='%b %Y')
df = df.sort_values(by=['client_name', 'file_name'])

# Calculate AUM increase month to month for each client
df['aum_increase'] = df.groupby('client_name')['total_aum'].diff().gt(0)

# Determine the majority condition dynamically for each client
# Group by client and calculate the count of `aum_increase` and the sum of True values
client_revenue_status = (
    df[df['waived'] == 'Yes']  # Filter only clients with waiver as "Yes"
    .groupby('client_name')
    .agg(
        total_months=('aum_increase', 'size'),
        increase_months=('aum_increase', 'sum')
    )
)

# Determine if each client has majority increase
client_revenue_status['is_revenue_generating'] = client_revenue_status.apply(
    lambda x: x['increase_months'] >= np.ceil(x['total_months'] / 2), axis=1
)

# Filter for only revenue-generating clients
revenue_generating_clients = client_revenue_status[client_revenue_status['is_revenue_generating']]

# Calculate the total waived amount for these clients
revenue_clients_df = (
    df[(df['client_name'].isin(revenue_generating_clients.index)) & (df['waived'] == 'Yes')]
    .groupby('client_name', as_index=False)['waived_amount']
    .sum()
)

# Rename columns for clarity
revenue_clients_df.rename(columns={'waived_amount': 'total_waived_amount'}, inplace=True)

# Output the resulting DataFrame
print(revenue_clients_df)
