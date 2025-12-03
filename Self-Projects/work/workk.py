import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ===================== CONFIG ===================== #
INPUT_FILE = r"input_today.xlsx"     # your current file with only today's snapshot
OUTPUT_FILE = r"simulated_snapshots.xlsx"

CASE_COL = "case_report"
STATUS_COL = "Pending with Status"
FILE_DATE_COL = "File Date"

N_DAYS = 30                # maximum number of days to simulate
MIN_HISTORY_FRACTION = 0.3 # each case will have between 30% of N_DAYS and N_DAYS rows
RANDOM_SEED = 42
# ================================================== #

def simulate_snapshots(df: pd.DataFrame,
                       case_col: str,
                       status_col: str,
                       file_date_col: str,
                       n_days: int,
                       min_history_fraction: float = 0.3,
                       seed: int = 42) -> pd.DataFrame:
    """
    From a single-day snapshot, simulate multiple days of history.

    - Each unique case in `case_col` gets a random number of days between
      `n_days * min_history_fraction` and `n_days`.
    - For each day, all other columns are kept static.
    - `status_col` is randomly sampled from the list of all statuses.
    - File dates go **backwards from today** (older dates = higher ageing).
    """
    rng = np.random.default_rng(seed)

    # Today (normalized to remove time)
    today = pd.Timestamp(datetime.today().date())

    # Ensure original snapshot has today's date
    df = df.copy()
    df[file_date_col] = today

    # List of all possible statuses to sample from
    status_values = df[status_col].dropna().unique().tolist()
    if not status_values:
        raise ValueError("No non-null values found in 'Pending with Status' column.")

    # We assume one row per case in today's file
    # If there are duplicates per case, this still works row-wise.
    min_days = max(1, int(n_days * min_history_fraction))
    max_days = n_days

    rows = []

    for idx, row in df.iterrows():
        # Random number of days for this case
        num_days = rng.integers(low=min_days, high=max_days + 1)

        # Create contiguous history from (today - (num_days-1)) to today
        for offset in range(num_days):
            snapshot_row = row.copy()

            # Oldest date first
            date_for_row = today - pd.Timedelta(days=(num_days - 1 - offset))
            snapshot_row[file_date_col] = date_for_row

            # For historical days, randomise status; for today's date you can keep original
            if date_for_row < today:
                snapshot_row[status_col] = rng.choice(status_values)

            rows.append(snapshot_row)

    simulated_df = pd.DataFrame(rows)

    # Sort nicely for sanity
    simulated_df = simulated_df.sort_values([case_col, file_date_col]).reset_index(drop=True)

    return simulated_df


def main():
    # Load today's file (csv / excel depending on what you use)
    # If your file is CSV, use: pd.read_csv(INPUT_FILE)
    df_today = pd.read_excel(INPUT_FILE)

    simulated_df = simulate_snapshots(
        df_today,
        case_col=CASE_COL,
        status_col=STATUS_COL,
        file_date_col=FILE_DATE_COL,
        n_days=N_DAYS,
        min_history_fraction=MIN_HISTORY_FRACTION,
        seed=RANDOM_SEED
    )

    # Save to Excel / CSV
    simulated_df.to_excel(OUTPUT_FILE, index=False)
    print(f"Simulated snapshots saved to: {OUTPUT_FILE}")
    print(simulated_df.head())


if __name__ == "__main__":
    main()