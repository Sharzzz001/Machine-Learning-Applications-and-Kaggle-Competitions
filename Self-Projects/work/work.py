# Convert TRADE_DATE to datetime
df['TRADE_DATE'] = pd.to_datetime(df['TRADE_DATE'], format='%d-%b-%y')

# Convert VERIFICATION_TIME to datetime and extract the date part
df['VERIFICATION_DATE'] = pd.to_datetime(df['VERIFICATION_TIME'], format='%d-%b-%y %I.%M.%S.%f %p').dt.date

# Calculate the difference in days
df['DAYS_DIFF'] = (df['VERIFICATION_DATE'] - df['TRADE_DATE'].dt.date).dt.days

# Create the flag for Days >= 2
df['FLAG_DAYS_GTE_2'] = df['DAYS_DIFF'] >= 2

print(df)
