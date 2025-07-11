def truncate_on_completion_list(group, status_col, completion_statuses):
    group = group.sort_values('Date')
    completion_idx = group[group[status_col].isin(completion_statuses)].first_valid_index()
    if completion_idx is not None:
        group = group.loc[:completion_idx]  # Keep the row with completed status
    return group