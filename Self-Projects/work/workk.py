def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if col in ("FileDate", "LoadTimestamp"):
            continue

        df[col] = (
            df[col]
            .astype(str)
            .replace({"NaT": None, "nan": None, "None": None})
        )

    return df
    
def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    df["FileDate"] = pd.to_datetime(df["FileDate"], errors="coerce").dt.date
    df["LoadTimestamp"] = pd.to_datetime(df["LoadTimestamp"], errors="coerce")

    return df

df = load_incremental_files(FOLDER_PATH, last_loaded_date)
df = sanitize_dataframe(df)
df = normalize_dates(df)
insert_into_access(df)