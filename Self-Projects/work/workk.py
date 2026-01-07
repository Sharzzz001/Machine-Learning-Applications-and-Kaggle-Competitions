uid_date_bounds = (
    df.groupby("uid")[FILE_DATE_COL]
      .agg(first_file_date="min", last_file_date="max")
)


uid_date_bounds["Total Ageing"] = np.busday_count(
    uid_date_bounds["first_file_date"].values.astype("datetime64[D]"),
    (uid_date_bounds["last_file_date"] + pd.Timedelta(days=1))
        .values.astype("datetime64[D]")
)

uid_date_bounds = uid_date_bounds[["Total Ageing"]]

final_df = (
    doc_pivot
    .join(ns_pivot, how="outer")
    .join(latest_status_df, how="left")
    .join(static_df, how="left")
    .join(uid_date_bounds, how="left")
    .reset_index()
)

