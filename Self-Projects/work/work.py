# Forward fill the 'Grouping' and 'Location' columns
sheet1_df['Grouping'] = sheet1_df['Grouping'].fillna(method='ffill')
sheet1_df['Location'] = sheet1_df['Location'].fillna(method='ffill')

# Filter rows where 'BPKey' is not null, as these correspond to client rows
client_rows = sheet1_df[sheet1_df['BPKey'].notna()]

# Drop unnecessary columns (e.g., 'Date') and reset the index
formatted_df = client_rows[['Grouping', 'Location', 'BPKey', 'Cash', 'Deposit', 'Share', 'Total AUM']]
formatted_df = formatted_df.rename(columns={"Grouping": "RM", "BPKey": "BP Name"}).reset_index(drop=True)

# Display the final formatted DataFrame
formatted_df.head()
