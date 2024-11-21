import pandas as pd

# Load the datasets
aum_df = pd.read_excel("monthly_client_aum.xlsx")  # File 1
trade_df = pd.read_excel("trade_volume.xlsx")     # File 2

# Preprocess AUM Data
aum_df['Month'] = pd.to_datetime(aum_df['Month'], format='%b %Y')  # Convert month to datetime
aum_df = aum_df.sort_values(['BP Key', 'Month'])  # Sort by client and month

# Preprocess Trade Volume Data
trade_df['Value Date'] = pd.to_datetime(trade_df['Value Date'], format='%d.%m.%Y')  # Convert to datetime
trade_count = trade_df.groupby('BP Key')['Value Date'].count().reset_index()  # Count trades per client
trade_count.rename(columns={'Value Date': 'Trade Count'}, inplace=True)

# Bin clients into High, Medium, and Low volume traders
trade_count['Trade Volume Category'] = pd.qcut(trade_count['Trade Count'], q=3, labels=['Low', 'Medium', 'High'])

# Merge Trade Volume Categories with AUM Data
aum_with_trades = pd.merge(aum_df, trade_count, on='BP Key', how='left')

# Check for consistent AUM growth month-on-month
aum_with_trades['AUM Growth'] = aum_with_trades.groupby('BP Key')['AUM'].diff().gt(0)  # Check if AUM increased
aum_growth_summary = (
    aum_with_trades.groupby('BP Key')
    .agg(
        total_months=('AUM Growth', 'size'),
        increasing_months=('AUM Growth', 'sum'),
        trade_volume_category=('Trade Volume Category', 'first')
    )
    .reset_index()
)

# Filter clients with consistent growth
aum_growth_summary['Consistent Growth'] = aum_growth_summary['increasing_months'] == aum_growth_summary['total_months']

# Calculate the percentage of clients with consistent growth in each category
growth_percentage = (
    aum_growth_summary.groupby('trade_volume_category')['Consistent Growth']
    .mean()
    .mul(100)
    .reset_index()
)

# Rename columns for clarity
growth_percentage.rename(columns={'Consistent Growth': 'Percentage of Clients with Consistent Growth'}, inplace=True)

# Output the results
print(growth_percentage)