import pandas as pd
from datetime import datetime

# Load the dataframes
df = pd.read_excel("df.xlsx")
df1 = pd.read_excel("df1.xlsx")

# Merge dataframes on BPKey
merged_df = pd.merge(df, df1, left_on="BPKey", right_on="Account Number", how="left")

# Convert 'Year Month' and 'Account Close Date' to datetime for analysis
merged_df['Year Month'] = pd.to_datetime(merged_df['Year Month'], format='%Y-%m')
merged_df['Account Close Date'] = pd.to_datetime(merged_df['Account Close Date'])

# Get today's date for comparison
today = pd.Timestamp(datetime.now().date())

# Filter clients who have left (Account Close Date < today)
left_clients_df = merged_df[merged_df['Account Close Date'].notna() & (merged_df['Account Close Date'] < today)]

# Analyze trends for clients who have left
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

# Apply trend analysis to each BPKey group for clients who have left
left_clients_df['Reason for Leaving'] = left_clients_df.groupby('BPKey').apply(lambda group: analyze_trends(group)).reset_index(drop=True)

# Save the analysis results to an Excel file
output_file = "bp_leaving_analysis_with_close_date.xlsx"
left_clients_df.to_excel(output_file, index=False)

print(f"Analysis complete. Results saved to {output_file}")
