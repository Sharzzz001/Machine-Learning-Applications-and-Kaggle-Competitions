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