import pandas as pd

# Consolidate data from all sheets with a 'Year Month' column
excel_file = "your_file.xlsx"
sheets = pd.ExcelFile(excel_file).sheet_names

consolidated_df = pd.DataFrame()
for sheet in sheets:
    # Load each sheet
    df = pd.read_excel(excel_file, sheet_name=sheet)
    # Extract month and year from sheet name and add it as a column
    year_month = f"2024-{sheet.split()[1]}"
    df['Year Month'] = year_month
    consolidated_df = pd.concat([consolidated_df, df], ignore_index=True)

# Calculate AUM growth by client and asset type month on month
consolidated_df = consolidated_df.sort_values(['BPKey', 'Year Month'])
aum_columns = ['Cash', 'Deposit', 'Share Bond', 'Struct. Prod.', 'Derivatives', 'Fund', 'Other', 'Total AUM']

# Calculate month-on-month differences for each asset type
for col in aum_columns:
    consolidated_df[f'{col}_growth'] = consolidated_df.groupby('BPKey')[col].diff()

# Filter for positive growth
positive_growth_df = consolidated_df[(consolidated_df[aum_columns].gt(0)).any(axis=1)]

# Summarize the total and percentage growth by asset type for each client
summary_df = positive_growth_df.groupby('BPKey')[[f'{col}_growth' for col in aum_columns]].sum()

# Calculate percentage contribution by asset type
summary_df_pct = summary_df.div(summary_df.sum(axis=1), axis=0) * 100

# Output to a new Excel file for review
with pd.ExcelWriter("consolidated_and_analyzed.xlsx") as writer:
    consolidated_df.to_excel(writer, sheet_name="Consolidated Data", index=False)
    summary_df.to_excel(writer, sheet_name="AUM Growth Summary")
    summary_df_pct.to_excel(writer, sheet_name="Growth Contribution %")

print("Consolidation and analysis complete. Check 'consolidated_and_analyzed.xlsx' for results.")
