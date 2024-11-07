import pandas as pd

# Sample data
data = {
    'client_name': ['Client A', 'Client A', 'Client A', 'Client B', 'Client B', 'Client B', 'Client C', 'Client C', 'Client C'],
    'waived': ['Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'Yes', 'Yes', 'Yes'],
    'total_aum': [100, 105, 110, 150, 145, 155, 120, 125, 123],
    'file_name': ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Jan 2024', 'Feb 2024', 'Mar 2024', 'Jan 2024', 'Feb 2024', 'Mar 2024']
}

df = pd.DataFrame(data)

# Convert file_name to datetime to sort by month
df['file_name'] = pd.to_datetime(df['file_name'], format='%b %Y')
df = df.sort_values(by=['client_name', 'file_name'])

# Calculate AUM increase month to month for each client
df['aum_increase'] = df.groupby('client_name')['total_aum'].diff().gt(0)

# Aggregate the revenue-generating status for each client
client_revenue_status = (
    df[df['waived'] == 'Yes']  # Filter only clients with waiver as "Yes"
    .groupby('client_name')['aum_increase']
    .apply(lambda x: x.sum() >= 5)  # Check if majority of months have an increase
)

# Count the number of revenue-generating clients with waiver "Yes"
revenue_generating_clients_count = client_revenue_status.sum()

# Output the result
print("Number of revenue-generating clients with waiver 'Yes':", revenue_generating_clients_count)