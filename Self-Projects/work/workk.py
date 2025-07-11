def remove_outliers_iqr(df, column):
    """
    Removes outliers from a DataFrame using the IQR method for a specific column.

    Parameters:
        df (pd.DataFrame): Input DataFrame
        column (str): Column name on which to apply the IQR filter

    Returns:
        pd.DataFrame: DataFrame without outliers
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_fence = Q1 - 1.5 * IQR
    upper_fence = Q3 + 1.5 * IQR

    df_filtered = df[(df[column] >= lower_fence) & (df[column] <= upper_fence)]
    return df_filtered