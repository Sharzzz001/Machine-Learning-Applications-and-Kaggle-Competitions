import pandas as pd

# Load the Excel file
excel_file = 'your_isin_file.xlsx'
df = pd.read_excel(excel_file)

# Initialize lists to store the extracted data
isins = []
trader_names_list = []
usd_diffs = []
percent_diffs = []

# Variables to hold current ISIN and trader names
current_isin = None
trader_names = []

# Loop through the DataFrame to group ISINs and extract necessary data
for idx, row in df.iterrows():
    isin = row['ISIN']
    trader = row['Trader name']
    
    # If ISIN is not NaN, this is part of the ISIN group
    if pd.notna(isin):
        if current_isin is None:  # Start a new ISIN group
            current_isin = isin
        trader_names.append(trader)
    
    # If ISIN is NaN, it indicates the blank row with difference data
    elif pd.isna(isin) and pd.isna(trader):
        if current_isin:  # Finalize the group for the current ISIN
            # Append the data for the ISIN group
            isins.append(current_isin)
            trader_names_list.append(', '.join(trader_names))  # Concatenate trader names
            usd_diffs.append(row['Diff'])  # Extract USD Difference
            percent_diffs.append(row['%diff'])  # Extract % Difference
            
            # Reset for the next group
            current_isin = None
            trader_names = []

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