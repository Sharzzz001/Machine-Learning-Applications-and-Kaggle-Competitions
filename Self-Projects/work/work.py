import pandas as pd

# Assuming the data is loaded in df with columns: BPKey, Total Fees, Year Month
# Example dataframe load
file_path = '/mnt/data/your_file.xlsx'  # Update with your file path
df = pd.read_excel(file_path)

# Convert 'Year Month' to datetime for proper sorting
df['Year Month'] = pd.to_datetime(df['Year Month'], format='%b %Y')

# Sort by BPKey and Year Month to track when each client appeared
df = df.sort_values(by=['BPKey', 'Year Month'])

# Identify the first month for each BPKey (this is their "onboarding" month)
df['First Month'] = df.groupby('BPKey')['Year Month'].transform('min')

# Create a new column that flags whether the client received a waiver (Total Fees = 0)
df['Waiver Granted'] = df['Total Fees'] == 0

# Initialize a list to store the results
results = []

# Loop through each month (from March to October)
for month in pd.date_range('2024-03-01', '2024-10-01', freq='MS'):
    # Filter data for this month
    df_month = df[df['Year Month'] == month]
    
    # Identify new clients in this month (clients who appear for the first time in this month)
    new_clients = df_month[df_month['First Month'] == month]
    
    # Identify older clients (clients who appeared before this month)
    older_clients = df_month[df_month['First Month'] < month]
    
    # Calculate percentage of new clients who received waivers
    new_waivers = new_clients['Waiver Granted'].sum()
    new_clients_count = new_clients['BPKey'].nunique()
    new_waiver_percentage = (new_waivers / new_clients_count) * 100 if new_clients_count > 0 else 0
    
    # Calculate percentage of older clients who received waivers
    older_waivers = older_clients['Waiver Granted'].sum()
    older_clients_count = older_clients['BPKey'].nunique()
    older_waiver_percentage = (older_waivers / older_clients_count) * 100 if older_clients_count > 0 else 0
    
    # Store results for this month
    results.append({
        'Month': month.strftime('%b %Y'),
        'New Clients Waiver Percentage': new_waiver_percentage,
        'Older Clients Waiver Percentage': older_waiver_percentage,
        'Difference in Waiver Percentage': new_waiver_percentage - older_waiver_percentage
    })

# Convert the results into a DataFrame
results_df = pd.DataFrame(results)

# Display or save the results
print(results_df)

# Optionally, save the results to a new Excel file
output_path = '/mnt/data/Waiver_Comparison_Monthly.xlsx'
results_df.to_excel(output_path, index=False)
print(f"Comparison saved at: {output_path}")
