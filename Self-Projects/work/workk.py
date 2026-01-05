import pandas as pd
from pathlib import Path
import re
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
INPUT_FOLDER = Path(r"D:\RR_SOW_Files")   # change this
OUTPUT_FILE = Path(r"D:\RR_SOW_MERGED.xlsx")

FILENAME_PATTERN = r"RR_SOW_(\d{2}-\d{2}-\d{4})\.xlsx"

# -----------------------------
# PROCESS FILES
# -----------------------------
all_dfs = []

for file in INPUT_FOLDER.glob("*.xlsx"):
    match = re.match(FILENAME_PATTERN, file.name)
    if not match:
        print(f"Skipping file (name format mismatch): {file.name}")
        continue

    # Extract date from filename
    file_date = datetime.strptime(match.group(1), "%d-%m-%Y").date()

    # Read Excel
    df = pd.read_excel(file)

    # Rename Title → AccountNumber
    if "Title" not in df.columns:
        raise ValueError(f"'Title' column missing in {file.name}")

    df = df.rename(columns={"Title": "AccountNumber"})

    # Add file date column
    df["FileDate"] = file_date

    all_dfs.append(df)

# -----------------------------
# MERGE & SAVE
# -----------------------------
if not all_dfs:
    raise RuntimeError("No valid files found to merge.")

final_df = pd.concat(all_dfs, ignore_index=True)

final_df.to_excel(OUTPUT_FILE, index=False)

print(f"Merged file saved to: {OUTPUT_FILE}")
print(f"Total rows: {len(final_df)}")