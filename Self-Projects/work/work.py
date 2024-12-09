# Convert TRADE_DATE to datetime
df['TRADE_DATE'] = pd.to_datetime(df['TRADE_DATE'], format='%d-%b-%y')

# Convert VERIFICATION_TIME to datetime and extract the date part
df['VERIFICATION_DATE'] = pd.to_datetime(df['VERIFICATION_TIME'], format='%d-%b-%y %I.%M.%S.%f %p').dt.date

# Function to calculate business days
def business_days_diff(start_date, end_date):
    # Generate a range of dates from start_date to end_date
    date_range = pd.date_range(start=start_date, end=end_date)
    # Filter out weekends (Monday=0, Sunday=6)
    business_days = date_range[~date_range.weekday.isin([5, 6])]
    return len(business_days) - 1  # Subtract 1 because start_date is inclusive

# Calculate business day difference
df['DAYS_DIFF'] = df.apply(lambda row: business_days_diff(row['TRADE_DATE'], row['VERIFICATION_DATE']), axis=1)

# Create the flag for Days >= 2
df['FLAG_DAYS_GTE_2'] = df['DAYS_DIFF'] >= 2
