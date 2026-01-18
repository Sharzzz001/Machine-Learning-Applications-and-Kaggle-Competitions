def compute_latest_status_ageing(case_df):
    case_df = case_df.sort_values(DATE_COL)

    latest_status = case_df[STATUS_COL].iloc[-1]

    reversed_df = case_df.iloc[::-1]

    ageing = 0

    for _, row in reversed_df.iterrows():
        if row[STATUS_COL] == latest_status:
            ageing += row["Row_Ageing"]
        else:
            break

    return ageing