import os
import pandas as pd
from datetime import datetime, timedelta
from pandas.tseries.offsets import BDay  # Business Day offset

def process_files(folder_path):
    # Initialize storage for final results
    results = []

    # Loop through all files in the folder
    for file_name in os.listdir(folder_path):
        # Check if the file name contains "AM" or "PM"
        if "AM" in file_name or "PM" in file_name:
            # Extract the date from the file name (assumes date is at position Dec 4 2024)
            try:
                file_date_str = " ".join(file_name.split()[-3:])  # Extract "Dec 4 2024"
                file_date = datetime.strptime(file_date_str, "%b %d %Y").date()
            except Exception as e:
                print(f"Error parsing date for file {file_name}: {e}")
                continue

            # Determine if file is Blotter or Bloomberg
            file_path = os.path.join(folder_path, file_name)
            try:
                df = pd.read_excel(file_path)
                if "Blotter" in file_name:
                    trade_date_col = "Trade Dt"
                elif "Bloomberg" in file_name:
                    trade_date_col = "Trade Date"
                else:
                    print(f"Unknown file type for {file_name}, skipping...")
                    continue
                
                # Ensure the required column exists
                if trade_date_col not in df.columns:
                    print(f"Column {trade_date_col} not found in {file_name}, skipping...")
                    continue
                
                # Parse the Trade Date column as datetime
                df[trade_date_col] = pd.to_datetime(df[trade_date_col]).dt.date
                
                # Calculate the business day offsets
                minus_1_bday = file_date - BDay(1)  # -1 business day
                plus_1_bday = file_date + BDay(1)   # +1 business day

                # Classify Trade Dates
                counts = {
                    "Date": file_date,
                    "Older than -1 days": sum(df[trade_date_col] < minus_1_bday.date()),
                    "-1 days": sum(df[trade_date_col] == minus_1_bday.date()),
                    "Same day": sum(df[trade_date_col] == file_date),
                    "+1 days": sum(df[trade_date_col] == plus_1_bday.date()),
                    "More than +1 days": sum(df[trade_date_col] > plus_1_bday.date())
                }
                
                results.append(counts)

            except Exception as e:
                print(f"Error processing file {file_name}: {e}")

    # Create final summary dataframe
    summary_df = pd.DataFrame(results)
    return summary_df

# Specify the folder path
folder_path = r"C:\path\to\your\folder"

# Call the function and get the summary dataframe
final_df = process_files(folder_path)

# Save the summary to an Excel file
output_file = "Final_Summary.xlsx"
final_df.to_excel(output_file, index=False)

print(f"Summary saved to {output_file}")