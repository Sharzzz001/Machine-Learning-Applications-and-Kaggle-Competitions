import pandas as pd
import numpy as np

# Load the datasets
aum_df = pd.read_excel("monthly_client_aum.xlsx")  # File 1
trade_df = pd.read_excel("trade_volume.xlsx")     # File 2

# Preprocess AUM Data
aum_df['Month'] = pd.to_datetime(aum_df['Month'], format='%b %Y')  # Convert month to datetime
aum_df = aum_df.sort_values(['BP Key', 'Month'])  # Sort by client and month

# Calculate AUM Growth
aum_df['AUM Growth'] = aum_df.groupby('BP Key')['AUM'].diff().gt(0)  # True if AUM increases

# Count total months and increasing months for each client
aum_growth_summary = (
    aum_df.groupby('BP Key')
    .agg(total_months=('AUM Growth', 'size'), increasing_months=('AUM Growth', 'sum'))
    .reset_index()
)

# Determine the dynamic threshold for each client
aum_growth_summary['growth_threshold'] = np.ceil((aum_growth_summary['total_months'] - 1) * 0.5)

# Flag clients with sufficient growth
aum_growth_summary['Is Growth Client'] = (
    aum_growth_summary['increasing_months'] >= aum_growth_summary['growth_threshold']
)

# Preprocess Trade Volume Data
trade_df['Value Date'] = pd.to_datetime(trade_df['Value Date'], format='%d.%m.%Y')  # Convert to datetime
trade_count = trade_df.groupby('BP Key')['Value Date'].count().reset_index()  # Count trades per client
trade_count.rename(columns={'Value Date': 'Trade Count'}, inplace=True)

# Bin clients into High, Medium, and Low volume traders
trade_count['Trade Volume Category'] = pd.qcut(trade_count['Trade Count'], q=3, labels=['Low', 'Medium', 'High'])

# Merge Trade Volume Categories with AUM Growth Summary
final_df = trade_count.merge(aum_growth_summary, on='BP Key', how='inner')

# Calculate Percentage of Growth Clients in Each Trade Volume Category
category_summary = (
    final_df.groupby('Trade Volume Category')
    .agg(
        total_clients=('BP Key', 'size'),
        growth_clients=('Is Growth Client', 'sum')
    )
    .reset_index()
)

category_summary['Percentage Growth Clients'] = (
    category_summary['growth_clients'] / category_summary['total_clients'] * 100
)

# Output Results
print(category_summary)