import os
import re

file_dict = {}

for f in os.listdir(folder_path):
    if f.endswith('.xlsx'):
        match = re.search(r'(\d{4}-\d{2}-\d{2})', f)
        if match:
            date = match.group(1)
            file_dict[date] = f  # Map date string to filename

# Get unique dates from main_df
unique_dates = main_df['Date'].dt.strftime('%Y-%m-%d').unique()

# Filter and sort target files
target_files = [file_dict[date] for date in unique_dates if date in file_dict]
target_files = sorted(target_files, key=lambda x: re.search(r'(\d{4}-\d{2}-\d{2})', x).group(1), reverse=True)