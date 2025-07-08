import pandas as pd
import os
import re
from datetime import datetime

# === CONFIGURATION ===
folder_path = r'C:\Path\To\Folder'  # Folder with Output1_YYYY-MM-DD.xlsx files
main_df = pd.read_excel(r'C:\Path\To\Main.xlsx')  # Main file with Account IDs only
main_df['Sales Code'] = None
main_df['EKYC ID'] = None

# === STEP 1: Get all output files sorted by date descending ===
pattern = re.compile(r'Output1_(\d{4}-\d{2}-\d{2})\.xlsx')
file_date_paths = []

for fname in os.listdir(folder_path):
    match = pattern.match(fname)
    if match:
        date = datetime.strptime(match.group(1), '%Y-%m-%d')
        full_path = os.path.join(folder_path, fname)
        file_date_paths.append((date, full_path))

# Sort by most recent first
file_date_paths.sort(reverse=True)

# === STEP 2: Build a dictionary to hold data as we find it ===
found_data = {}  # key: account id → value: (Sales Code, EKYC ID)

# === STEP 3: Iterate through files, updating only unmatched IDs ===
unmatched_ids = set(main_df['Account ID'])

for date, path in file_date_paths:
    if not unmatched_ids:
        break  # All found

    print(f"Looking in file: {os.path.basename(path)}")
    try:
        df = pd.read_excel(path)
    except Exception as e:
        print(f"Failed to read {path}: {e}")
        continue

    # Filter rows with account ids we're still looking for
    df = df[['Account ID', 'Sales Code', 'EKYC ID']].dropna(subset=['Account ID'])
    df = df[df['Account ID'].isin(unmatched_ids)]

    for _, row in df.iterrows():
        acc_id = row['Account ID']
        sales = row['Sales Code']
        ekyc = row['EKYC ID']
        found_data[acc_id] = (sales, ekyc)
        unmatched_ids.discard(acc_id)

# === STEP 4: Fill main_df using the found_data dict ===
main_df['Sales Code'] = main_df['Account ID'].map(lambda x: found_data.get(x, (None, None))[0])
main_df['EKYC ID'] = main_df['Account ID'].map(lambda x: found_data.get(x, (None, None))[1])

# === STEP 5: Export or continue ===
main_df.to_excel('main_with_merged_data.xlsx', index=False)
print("✅ Done. Output written to 'main_with_merged_data.xlsx'")