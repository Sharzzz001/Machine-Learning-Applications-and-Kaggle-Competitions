sheet1_df['Grouping'] = sheet1_df['Grouping'].fillna(method='ffill')
sheet1_df['Location'] = sheet1_df['Location'].fillna(method='ffill')

# Identify rows where BPKey is not null (client rows)
client_rows = sheet1_df[sheet1_df['BPKey'].notna()].copy()

# Create a condition for when the 'Grouping' column doesn't have a number followed by a hyphen (e.g., '787 - ABC')
condition_rm = sheet1_df['Grouping'].str.contains(r'^\d+ -', na=False)

# Assign RM names where the condition is True (i.e., numbers followed by hyphen)
sheet1_df['RM'] = sheet1_df['Grouping'].where(condition_rm)

# Backfill RM even if not NaN where the condition is met
sheet1_df['RM'] = sheet1_df['RM'].fillna(method='ffill')

# Assign RM name to client rows
client_rows['RM'] = sheet1_df.loc[client_rows.index, 'RM']

# Assign BP Name to client rows (this is the 'Grouping' value for client rows)
client_rows['BP Name'] = client_rows['Grouping']

# Ensure RM values are correctly assigned only from rows where Location is filled
client_rows['RM'] = client_rows['RM'].where(client_rows['RM'] != client_rows['BP Name'])

# Select and reorder columns for the final output
formatted_df = client_rows[['RM', 'Location', 'BP Name', 'BPKey', 'Cash', 'Deposit', 'Share', 'Total AUM']]

# Reset index for clean output
formatted_df = formatted_df.reset_index(drop=True)

# Display the formatted DataFrame
print(formatted_df)
