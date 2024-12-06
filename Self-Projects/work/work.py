import numpy as np
from datetime import datetime, timedelta

def calculate_time_diff(row):
    """Calculate time difference excluding weekend window."""
    start_time = row['CONFIRM_EXECUTION_TIME']
    end_time = row['VERIFICATION_TIME']
    
    if pd.isna(start_time) or pd.isna(end_time):
        return np.nan  # Return NaN if either timestamp is missing
    
    total_diff = (end_time - start_time).total_seconds() / 3600  # Calculate initial time difference in hours
    
    # Define weekend window (Saturday 5 AM to Monday 8 AM)
    weekend_start = start_time.replace(hour=5, minute=0, second=0, microsecond=0) + timedelta((5 - start_time.weekday()) % 7)
    weekend_end = weekend_start + timedelta(days=2, hours=3)
    
    # Calculate overlap with the weekend window
    overlap_start = max(start_time, weekend_start)
    overlap_end = min(end_time, weekend_end)
    
    if overlap_start < overlap_end:  # If overlap exists
        weekend_overlap = (overlap_end - overlap_start).total_seconds() / 3600
    else:
        weekend_overlap = 0  # No overlap
    
    # Subtract weekend overlap from total time difference
    adjusted_diff = total_diff - weekend_overlap
    return adjusted_diff

# Apply the function to calculate adjusted time differences
df['TIME_DIFF_HOURS'] = df.apply(calculate_time_diff, axis=1)
