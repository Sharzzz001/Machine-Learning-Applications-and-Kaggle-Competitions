def autofit_columns(writer, df, sheet_name):
    """Auto-fit column widths in the given sheet based on df contents."""
    worksheet = writer.sheets[sheet_name]
    for idx, col in enumerate(df.columns):
        # Convert all values to string length
        series = df[col].astype(str)
        max_len = max((
            series.map(len).max(),
            len(str(col))
        )) + 2  # add a little extra padding
        worksheet.set_column(idx, idx, max_len)
        

with pd.ExcelWriter(out_filename, engine="xlsxwriter") as writer:
    # Pivot
    pivot.to_excel(writer, sheet_name="Pivot_Overview", startrow=0)
    autofit_columns(writer, pivot.reset_index(), "Pivot_Overview")

    # Add totals after pivot
    workbook  = writer.book
    worksheet = writer.sheets["Pivot_Overview"]
    nrows = pivot.shape[0] + 1
    insert_row = nrows + 2
    worksheet.write(insert_row, 0, "Total unique accounts")
    worksheet.write(insert_row, 1, agg["Account"].nunique())
    worksheet.write(insert_row + 1, 0, "Total reasons for blocked accounts")
    worksheet.write(insert_row + 1, 1, pivot["Total"].sum())

    # Other sheets
    agg.to_excel(writer, sheet_name="Account_Aggregated", index=False)
    autofit_columns(writer, agg, "Account_Aggregated")

    exploded.to_excel(writer, sheet_name="Account_Category", index=False)
    autofit_columns(writer, exploded, "Account_Category")

    combo_map = []
    for i, combo in enumerate(exploded["RemarkCombo"].unique(), start=1):
        sheet = f"Combo_{i}"
        subset_rows = exploded[exploded["RemarkCombo"] == combo].copy()
        subset_rows.to_excel(writer, sheet_name=sheet, index=False)
        autofit_columns(writer, subset_rows, sheet)
        combo_map.append({
            "Combo_Sheet": sheet,
            "RemarkCombo": combo,
            "Unique_Accounts": subset_rows["Account"].nunique()
        })

    combo_df = pd.DataFrame(combo_map)
    combo_df.to_excel(writer, sheet_name="Combo_Index", index=False)
    autofit_columns(writer, combo_df, "Combo_Index")