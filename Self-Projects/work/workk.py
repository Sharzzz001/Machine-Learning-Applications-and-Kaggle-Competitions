def compute_phased_aging(group, status_col, completed_value):
    group = group.sort_values('Date').copy()
    group['prev_status'] = group[status_col].shift()
    group['status_change'] = group[status_col] != group['prev_status']
    group['group_id'] = group['status_change'].cumsum()

    # Trim the group after first 'Completed' status (inclusive)
    if completed_value in group[status_col].values:
        completed_idx = group[group[status_col] == completed_value].first_valid_index()
        group = group.loc[:completed_idx]

    # Compute aging per status phase
    aging = group.groupby('group_id').agg({
        'Date': ['min', 'max'],
        status_col: 'first',
        'Account number': 'first'
    }).reset_index()

    aging.columns = ['group_id', 'Start_Date', 'End_Date', status_col, 'Account number']
    aging['Aging_Days'] = aging.apply(
        lambda row: np.busday_count(row['Start_Date'].date(), (row['End_Date'] + pd.Timedelta(days=1)).date()),
        axis=1
    )
    return aging
    
    
aging_doc = df_doc.groupby('Account number', group_keys=False).apply(
    lambda x: compute_phased_aging(x, 'Status', STATUS_COMPLETE)
)

aging_screen = df_screen.groupby('Account number', group_keys=False).apply(
    lambda x: compute_phased_aging(x, 'Status_screen', SCREEN_COMPLETE)
)

def average_age_per_status(group, status_col, completed_value):
    group = group.sort_values('Date').copy()
    group['prev_status'] = group[status_col].shift()
    group['hop_id'] = (group[status_col] != group['prev_status']).cumsum()

    # Trim on first completion
    if completed_value in group[status_col].values:
        idx = group[group[status_col] == completed_value].first_valid_index()
        group = group.loc[:idx]

    # Track aging per hop
    hops = group.groupby(['hop_id', status_col]).agg({
        'Date': ['min', 'max'],
        'Account number': 'first'
    }).reset_index()

    hops.columns = ['hop_id', status_col, 'Start_Date', 'End_Date', 'Account number']

    hops['Hop_Duration'] = hops.apply(
        lambda row: np.busday_count(row['Start_Date'].date(), (row['End_Date'] + pd.Timedelta(days=1)).date()),
        axis=1
    )

    # Aggregate per status
    result = hops.groupby(['Account number', status_col]).agg(
        Total_Days=('Hop_Duration', 'sum'),
        Hop_Count=('Hop_Duration', 'count')
    ).reset_index()

    result['Avg_Days_Per_Hop'] = result['Total_Days'] / result['Hop_Count']

    return result
    
aging_doc_avg = df_doc.groupby('Account number', group_keys=False).apply(
    lambda x: average_age_per_status(x, 'Status', STATUS_COMPLETE)
)

aging_screen_avg = df_screen.groupby('Account number', group_keys=False).apply(
    lambda x: average_age_per_status(x, 'Status_screen', SCREEN_COMPLETE)
)
