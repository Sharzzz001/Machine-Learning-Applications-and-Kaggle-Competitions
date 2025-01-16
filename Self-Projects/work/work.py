import pandas as pd

# Load the files
aum_file = "aum_file.xlsx"  # Replace with the actual AUM file path
joining_file = "joining_file.xlsx"  # Replace with the actual Joining Date file path

aum_df = pd.read_excel(aum_file)
joining_df = pd.read_excel(joining_file)

# Convert 'Year Month' and 'Joining Date' to datetime for calculations
aum_df['Year Month'] = pd.to_datetime(aum_df['Year Month'], format='%Y-%m')
joining_df['Joining Date'] = pd.to_datetime(joining_df['Joining Date'])

# Merge the data on BPKey
merged_df = pd.merge(joining_df, aum_df, on='BPKey', how='left')

# Group by BPKey and calculate the months to first AUM
def calculate_months_to_aum(sub_df):
    joining_date = sub_df['Joining Date'].iloc[0]
    aum_dates = sub_df['Year Month'].dropna().sort_values()

    if aum_dates.empty:
        # No AUM data for this BPKey
        return None

    first_aum_date = aum_dates.iloc[0]
    months_to_aum = (first_aum_date.year - joining_date.year) * 12 + (first_aum_date.month - joining_date.month)

    return max(0, months_to_aum)  # Ensure non-negative

# Apply the calculation
joining_df['Months Without AUM'] = merged_df.groupby('BPKey').apply(calculate_months_to_aum).reset_index(drop=True)

# Save the results to an Excel file
output_file = "months_without_aum.xlsx"
joining_df.to_excel(output_file, index=False)

print(f"Analysis complete. Results saved to {output_file}")