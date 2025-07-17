import pandas as pd
import os

found_data = {}

# Step 1: Standardize account numbers
main_df['Account Number'] = main_df['Account Number'].astype(str).str.strip()
unmatched_ids = set(main_df['Account Number'])

# Step 2: Get list of needed files based on dates
unique_dates = main_df['Date'].dt.strftime('%Y-%m-%d').unique()
file_dict = {f.split('.')[0]: f for f in os.listdir(folder_path) if f.endswith('.xlsx')}
target_files = [file_dict[date] for date in unique_dates if date in file_dict]

# Step 3: Sort files newest to oldest (reverse chronological)
target_files.sort(reverse=True)

# Step 4: Loop through relevant files
for file in target_files:
    if not unmatched_ids:
        break

    try:
        df = pd.read_excel(os.path.join(folder_path, file))
        df['Account Number'] = df['Account Number'].astype(str).str.strip()
        df = df[df['Account Number'].isin(unmatched_ids)]

        for _, row in df.iterrows():
            acc_id = row['Account Number']
            sales = row['Sales Code']
            ekyc = row['eKYC']
            found_data[acc_id] = (sales, ekyc)
            unmatched_ids.discard(acc_id)

    except Exception as e:
        print(f"Error reading {file}: {e}")

# Step 5: Map back to main_df
main_df['Sales Code'] = main_df['Account Number'].map(lambda x: found_data.get(x, (None, None))[0])
main_df['eKYC'] = main_df['Account Number'].map(lambda x: found_data.get(x, (None, None))[1])