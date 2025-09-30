with pd.ExcelWriter(out_filename) as writer:
    # Main outputs
    pivot.to_excel(writer, sheet_name="Pivot_Overview")
    agg.to_excel(writer, sheet_name="Account_Aggregated", index=False)
    exploded.to_excel(writer, sheet_name="Account_Category", index=False)

    # One sheet per combo, with mapping index
    combo_map = []
    for i, combo in enumerate(exploded["RemarkCombo"].unique(), start=1):
        sheet = f"Combo_{i}"
        combo_map.append({"Combo_Sheet": sheet, "RemarkCombo": combo})
        subset_rows = exploded[exploded["RemarkCombo"] == combo].copy()
        subset_rows.to_excel(writer, sheet_name=sheet, index=False)

    # Add mapping sheet
    pd.DataFrame(combo_map).to_excel(writer, sheet_name="Combo_Index", index=False)