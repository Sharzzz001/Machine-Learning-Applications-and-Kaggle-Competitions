import pandas as pd
import numpy as np

# Sample data
data = {
    "CONFIRM_EXECUTION_TIME": [None, "2024-01-29 15:00:00", "2024-01-29 08:00:00", None],
    "EXECUTION_TIME": ["2024-01-29 14:00:00", "2024-01-29 15:00:00", "2024-01-29 08:00:00", "2024-01-29 10:00:00"],
    "VERIFICATION_TIME": ["2024-01-30 05:00:00", "2024-01-29 18:00:00", "2024-01-29 23:00:00", None],
}

# Create DataFrame
df = pd.DataFrame(data)

# Convert times to datetime format
df["CONFIRM_EXECUTION_TIME"] = pd.to_datetime(df["CONFIRM_EXECUTION_TIME"])
df["EXECUTION_TIME"] = pd.to_datetime(df["EXECUTION_TIME"])
df["VERIFICATION_TIME"] = pd.to_datetime(df["VERIFICATION_TIME"])

# Fill NaN values in CONFIRM_EXECUTION_TIME with EXECUTION_TIME
df["CONFIRM_EXECUTION_TIME"] = df["CONFIRM_EXECUTION_TIME"].fillna(df["EXECUTION_TIME"])

# Calculate the time difference in hours only for rows where both CONFIRM_EXECUTION_TIME and VERIFICATION_TIME are not NaN
df["TIME_DIFF_HOURS"] = np.where(
    df["CONFIRM_EXECUTION_TIME"].notna() & df["VERIFICATION_TIME"].notna(),
    (df["VERIFICATION_TIME"] - df["CONFIRM_EXECUTION_TIME"]).dt.total_seconds() / 3600,
    np.nan
)

# Flag rows where the time difference is greater than 12 hours, otherwise False, and NaN where either time is NaN
df["NEXT_DAY_VERIFICATION"] = np.where(
    df["TIME_DIFF_HOURS"].isna(),
    np.nan,
    df["TIME_DIFF_HOURS"] > 12
)

# Display the DataFrame
print(df)
