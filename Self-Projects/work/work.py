import pandas as pd

# Load the Excel file
excel_file = 'your_isin_file.xlsx'
df = pd.read_excel(excel_file)

# Initialize lists to store the extracted data
isins = []
trader_names_list = []
usd_diffs = []
percent_diffs = []

# Loop through the DataFrame to group ISINs and extract necessary data
current_isin = None
trader_names = []

for idx, row in df.iterrows():
    isin = row['ISIN']
    
    # Check if the current row is an ISIN group (not empty)
    if pd.notna(isin):
        if current_isin:  # If we're done with the previous group
            # Append the data for the previous ISIN group
            isins.append(current_isin)
            trader_names_list.append(', '.join(trader_names))
            usd_diffs.append(df.loc[idx - 1, 'Difference'])  # USD Difference from the blank row
            percent_diffs.append(df.loc[idx - 1, '% diff'])  # % Difference from the blank row
        
        # Reset for the new ISIN group
        current_isin = isin
        trader_names = [row['Trader Name']]  # Start a new list of trader names
    
    # If the ISIN is NaN (meaning the row is a blank one), skip it
    elif pd.isna(isin) and current_isin:
        continue
    else:
        # Collect trader names for the current ISIN group
        trader_names.append(row['Trader Name'])

# Handle the last ISIN group after the loop ends
if current_isin:
    isins.append(current_isin)
    trader_names_list.append(', '.join(trader_names))
    usd_diffs.append(df.loc[len(df) - 1, 'Difference'])  # USD Difference from the last blank row
    percent_diffs.append(df.loc[len(df) - 1, '% diff'])  # % Difference from the last blank row

# Create a new DataFrame with the extracted data
result_df = pd.DataFrame({
    'ISIN': isins,
    'Trader Names': trader_names_list,
    'USD Difference': usd_diffs,
    '% Difference': percent_diffs
})

# Save the result to a new Excel file or display it
result_df.to_excel('processed_isin_data.xlsx', index=False)
print(result_df)