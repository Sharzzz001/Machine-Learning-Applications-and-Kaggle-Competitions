# --- replace the "write each remark combo" loop in step 8 with this ---
with pd.ExcelWriter(out_filename) as writer:
    pivot.to_excel(writer, sheet_name="Pivot_Overview")
    agg.to_excel(writer, sheet_name="Account_Aggregated", index=False)

    # Write exploded account-category data (this is what the pivot is built from!)
    exploded.to_excel(writer, sheet_name="Account_Category", index=False)

    # Also one sheet per combo, but *from exploded* so it reconciles with pivot
    combos = exploded["RemarkCombo"].unique()
    for combo in combos:
        sheet = sanitize_sheetname(combo)
        subset_rows = exploded[exploded["RemarkCombo"] == combo].copy()
        subset_rows.to_excel(writer, sheet_name=sheet, index=False)