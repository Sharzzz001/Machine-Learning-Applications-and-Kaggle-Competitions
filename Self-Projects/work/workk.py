import pandas as pd
from pathlib import Path
from datetime import datetime

# ================= CONFIG ================= #
FOLDER_PATH = r"D:\case_reports_snapshots"   # folder containing excel files
FILE_DATE_COL = "File Date"

# date format in filename: 11-12-2025
FILENAME_DATE_FORMAT = "%d-%m-%Y"
# ========================================= #


def extract_date_from_filename(filename: str) -> pd.Timestamp:
    """
    Extract date from filename like:
    'Case_Reports 11-12-2025.xlsx'
    """
    # Take the last part before .xlsx
    date_str = filename.replace(".xlsx", "").split()[-1]
    return pd.to_datetime(
        datetime.strptime(date_str, FILENAME_DATE_FORMAT)
    )


def load_and_merge_snapshots(folder_path: str) -> pd.DataFrame:
    all_dfs = []

    for file_path in Path(folder_path).glob("*.xlsx"):
        file_date = extract_date_from_filename(file_path.name)

        df = pd.read_excel(file_path)
        df[FILE_DATE_COL] = file_date

        all_dfs.append(df)

    if not all_dfs:
        raise ValueError("No Excel files found in the folder.")

    merged_df = pd.concat(all_dfs, ignore_index=True)
    return merged_df


# ================= RUN ================= #
df_snapshots = load_and_merge_snapshots(FOLDER_PATH)

print(df_snapshots.head())
print(df_snapshots[FILE_DATE_COL].min(), "→", df_snapshots[FILE_DATE_COL].max())