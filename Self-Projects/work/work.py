import os
import pandas as pd
from datetime import datetime

# === Configuration ===
input_folder = 'path/to/input_folder'           # Folder with daily output files
output_file = 'path/to/database/Master.xlsx'    # Path to the master database file
file_prefix = 'Output1_'                        # Common file prefix

# === Step 1: Get today's filename ===
today_str = datetime.today().strftime('%Y-%m-%d')
expected_filename = f'{file_prefix}{today_str}.xlsx'
expected_file_path = os.path.join(input_folder, expected_filename)

if not os.path.exists(expected_file_path):
    print(f"No file found for today: {expected_filename}")
    exit()

# === Step 2: Read today’s file and add date column ===
new_data = pd.read_excel(expected_file_path)
new_data['Date'] = today_str

# === Step 3: Load existing master database or create new ===
if os.path.exists(output_file):
    master_df = pd.read_excel(output_file)
else:
    master_df = pd.DataFrame()

# === Step 4: Check for existing data for today's date ===
if not master_df.empty and 'Date' in master_df.columns and today_str in master_df['Date'].astype(str).values:
    confirm = input(f"Data for {today_str} already exists. Overwrite? (y/n): ").lower()
    if confirm != 'y':
        print("Operation cancelled by user.")
        exit()
    else:
        # Remove today's data from master
        master_df = master_df[master_df['Date'].astype(str) != today_str]

# === Step 5: Append new data and save ===
updated_df = pd.concat([master_df, new_data], ignore_index=True)
updated_df.to_excel(output_file, index=False)
print(f"Data for {today_str} has been added to the master file.")