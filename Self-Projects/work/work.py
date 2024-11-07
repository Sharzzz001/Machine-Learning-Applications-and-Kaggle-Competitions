import pandas as pd
import numpy as np

# Sample data
data = {
    'client_name': ['Client A', 'Client A', 'Client A', 'Client B', 'Client B', 'Client B', 'Client C', 'Client C', 'Client C'],
    'waived': ['No', 'Yes', 'Yes', 'No', 'Yes', 'No', 'Yes', 'Yes', 'Yes'],
    'total_aum': [100, 105, 110, 150, 145, 155, 120, 125, 123],
    'file_name': ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Jan 2024', 'Feb 2024', 'Mar 2024', 'Jan 2024', 'Feb 2024', 'Mar 2024'],
    'Fees': [0.00125, 0, 0, 0.001, 0, 0.0011, 0, 0, 0]
}

df = pd.DataFrame(data)

# Convert `file_name` to datetime and sort by `client_name` and `file_name`
df['file_name'] = pd.to_datetime(df['file_name'], format='%b %Y')
df = df.sort_values(by=['client_name', 'file_name'])

# Step 1: Calculate the average fee for each client when waived = No
client_avg_fee = df[df['waived'] == 'No'].groupby('client_name')['Fees'].mean().to_dict()

# Step 2: Define a function to calculate waived amount based on average fee and total_aum
def calculate_waived_amount(row):
    if row['waived'] == 'Yes':
        avg_fee = client_avg_fee.get(row['client_name'], 0)  # Use 0 if no waived=No records for the client
        return avg_fee * row['total_aum'] / 12
    return 0

df['waived_amount'] = df.apply(calculate_waived_amount, axis=1)

# Step 3: Determine month-over-month AUM increase for each client
df['aum_increase'] = df.groupby('client_name')['total_aum'].diff().gt(0)

# Step 4: Check if clients have a majority of months with AUM increases
client_revenue_status = (
    df.groupby('client_name')
    .agg(
        total_months=('aum_increase', 'size'),
        increase_months=('aum_increase', 'sum')
    )
)

client_revenue_status['is_revenue_generating'] = client_revenue_status.apply(
    lambda x: x['increase_months'] >= np.ceil(x['total_months'] / 2), axis=1
)

# Step 5: Filter for revenue-generating clients and sum waived amounts
revenue_generating_clients = client_revenue_status[client_revenue_status['is_revenue_generating']].index

revenue_clients_df = (
    df[(df['client_name'].isin(revenue_generating_clients)) & (df['waived'] == 'Yes')]
    .groupby('client_name', as_index=False)['waived_amount']
    .sum()
)

# Rename columns for clarity
revenue_clients_df.rename(columns={'waived_amount': 'total_waived_amount'}, inplace=True)

# Add an estimate of total "lost" fees for revenue-generating clients if waiver was not applied
revenue_clients_df['hypothetical_fees_without_waiver'] = revenue_clients_df['total_waived_amount']  # Assuming waived amount represents potential revenue

# Output the resulting DataFrame
print(revenue_clients_df)
