with pd.ExcelWriter(out_filename) as writer:
    # ---- Pivot with 2-line gap + totals ----
    # First, write pivot starting at row 0
    pivot.to_excel(writer, sheet_name="Pivot_Overview", startrow=0)

    # Get totals
    total_unique_accounts = agg["Account"].nunique()
    total_reasons = pivot["Total"].sum()  # grand total across all categories

    # Re-open the sheet writer to append after pivot
    workbook  = writer.book
    worksheet = writer.sheets["Pivot_Overview"]

    # Find how many rows pivot took (rows + header)
    nrows = pivot.shape[0] + 1  # +1 for header row
    insert_row = nrows + 2      # leave 2 blank lines

    worksheet.write(insert_row, 0, "Total unique accounts")
    worksheet.write(insert_row, 1, total_unique_accounts)

    worksheet.write(insert_row + 1, 0, "Total reasons for blocked accounts")
    worksheet.write(insert_row + 1, 1, total_reasons)

    # ---- Other sheets as before ----
    agg.to_excel(writer, sheet_name="Account_Aggregated", index=False)
    exploded.to_excel(writer, sheet_name="Account_Category", index=False)

    combo_map = []
    for i, combo in enumerate(exploded["RemarkCombo"].unique(), start=1):
        sheet = f"Combo_{i}"
        combo_map.append({
            "Combo_Sheet": sheet,
            "RemarkCombo": combo,
            "Unique_Accounts": exploded.loc[exploded["RemarkCombo"] == combo, "Account"].nunique()
        })
        subset_rows = exploded[exploded["RemarkCombo"] == combo].copy()
        subset_rows.to_excel(writer, sheet_name=sheet, index=False)

    pd.DataFrame(combo_map).to_excel(writer, sheet_name="Combo_Index", index=False)