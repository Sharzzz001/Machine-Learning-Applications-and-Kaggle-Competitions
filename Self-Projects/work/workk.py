def cap_outliers_iqr(df, column):
    """
    Caps outliers in the given column using the IQR method (winsorizing).

    Values above upper fence are capped to upper fence,
    values below lower fence are capped to lower fence.
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_fence = Q1 - 1.5 * IQR
    upper_fence = Q3 + 1.5 * IQR

    df_capped = df.copy()
    df_capped[column] = df_capped[column].clip(lower=lower_fence, upper=upper_fence)
    return df_capped