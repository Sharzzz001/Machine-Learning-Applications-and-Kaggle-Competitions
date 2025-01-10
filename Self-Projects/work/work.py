import pandas as pd

# Load the dataframes
df = pd.read_excel("df.xlsx")
df1 = pd.read_excel("df1.xlsx")

# Merge dataframes on BPKey
merged_df = pd.merge(df, df1, left_on="BPKey", right_on="Account Number", how="left")

# Convert 'Year Month' to datetime for trend analysis
merged_df['Year Month'] = pd.to_datetime(merged_df['Year Month'], format='%Y-%m')

# Sort data by BPKey and Year Month
merged_df = merged_df.sort_values(by=['BPKey', 'Year Month'])

# Analyze trends for each BPKey
def analyze_trends(sub_df):
    # Check if TOTAL_AMOUNT_CONT is decreasing
    is_total_amt_decreasing = sub_df['TOTAL_AMOUNT_CONT'].is_monotonic_decreasing
    
    # Check if Total fees are increasing
    is_total_fees_increasing = sub_df['Total fees'].is_monotonic_increasing
    
    # Check if Waiver Granted frequency is decreasing
    waiver_granted_count = sub_df['Waiver Granted'].sum()
    is_waiver_granted_decreasing = waiver_granted_count < len(sub_df) / 2  # Compare to 50% threshold

    # Determine reason for leaving
    reason = []
    if is_total_amt_decreasing:
        reason.append("Decreasing TOTAL_AMOUNT_CONT")
    if is_total_fees_increasing:
        reason.append("Increasing Total fees")
    if is_waiver_granted_decreasing:
        reason.append("Decreasing Waivers")
    
    return ", ".join(reason) if reason else "Unknown"

# Apply trend analysis to each BPKey group
merged_df['Reason for Leaving'] = merged_df.groupby('BPKey').apply(analyze_trends).reset_index(drop=True)

# Save results to an Excel file
output_file = "bp_leaving_analysis.xlsx"
merged_df.to_excel(output_file, index=False)

print(f"Analysis complete. Results saved to {output_file}")
