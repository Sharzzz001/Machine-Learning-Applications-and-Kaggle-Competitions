def average_age_per_status(group, status_col, completion_statuses):
    group = group.sort_values('Date').copy()
    group['prev_status'] = group[status_col].shift()
    group['hop_id'] = (group[status_col] != group['prev_status']).cumsum()

    # Stop aging after first match in completion list
    if any(group[status_col].isin(completion_statuses)):
        idx = group[group[status_col].isin(completion_statuses)].first_valid_index()
        group = group.loc[:idx]

    # Compute hop-level aging
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