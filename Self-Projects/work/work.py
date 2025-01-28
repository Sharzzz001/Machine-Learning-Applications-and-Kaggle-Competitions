import os
import pandas as pd
from datetime import datetime
from pandas.tseries.offsets import BDay  # Business Day offset

def process_files(folder_path):
    # Initialize storage for final results
    results = []

    # Loop through all files in the folder
    for file_name in os.listdir(folder_path):
        # Process only Excel files
        if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
            # Extract the file date from the file name (assumes date is at position Dec 4 2024)
            try:
                file_date_str = " ".join(file_name.split()[-3:])  # Extract "Dec 4 2024"
                file_date = datetime.strptime(file_date_str, "%b %d %Y").date()
            except Exception as e:
                print(f"Error parsing date for file {file_name}: {e}")
                continue

            # Get the full file path
            file_path = os.path.join(folder_path, file_name)
            
            try:
                # Load the Excel file and check its sheet names
                excel_data = pd.ExcelFile(file_path)
                for sheet_name in excel_data.sheet_names:
                    # Determine if sheet is "Blotter" or "Bloomberg"
                    if sheet_name == "Blotter":
                        trade_date_col = "Trade Dt"
                    elif sheet_name == "Bloomberg":
                        trade_date_col = "Trade Date"
                    else:
                        continue  # Skip other sheets

                    # Load the relevant sheet into a DataFrame
                    df = pd.read_excel(file_path, sheet_name=sheet_name)

                    # Ensure the required column exists
                    if trade_date_col not in df.columns:
                        print(f"Column {trade_date_col} not found in sheet {sheet_name} of {file_name}, skipping...")
                        continue

                    # Parse the Trade Date column as datetime
                    df[trade_date_col] = pd.to_datetime(df[trade_date_col]).dt.date

                    # Calculate business day offsets
                    minus_1_bday = file_date - BDay(1)  # -1 business day
                    plus_1_bday = file_date + BDay(1)   # +1 business day

                    # Classify Trade Dates
                    counts = {
                        "Date": file_date,
                        "Sheet Name": sheet_name,
                        "Older than -1 days": sum(df[trade_date_col] < minus_1_bday.date()),
                        "-1 days": sum(df[trade_date_col] == minus_1_bday.date()),
                        "Same day": sum(df[trade_date_col] == file_date),
                        "+1 days": sum(df[trade_date_col] == plus_1_bday.date()),
                        "More than +1 days": sum(df[trade_date_col] > plus_1_bday.date())
                    }

                    # Append results
                    results.append(counts)

            except Exception as e:
                print(f"Error processing file {file_name}: {e}")

    # Create final summary DataFrame
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