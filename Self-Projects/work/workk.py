# -----------------------
# Only create sheets for non-NTS RemarkCombos used in pivot
# -----------------------
combo_map = []

# Get list of RemarkCombos used in pivot (exclude NTS)
combo_list_included = included_non_nts["RemarkCombo"].dropna().unique().tolist()

for i, combo in enumerate(combo_list_included, start=1):
    sheet_name = f"Combo_{i}"

    # Select rows for this combo (exclude NTS)
    subset = exploded[
        (exploded["RemarkCombo"] == combo) & (~exploded["is_nts"])
    ].copy()

    # Ensure non-empty DataFrame
    if subset.empty:
        subset = pd.DataFrame(columns=exploded.columns)

    # Write the sheet
    subset.to_excel(writer, sheet_name=sheet_name, index=False)
    autofit_columns(writer, subset, sheet_name)
    writer.sheets[sheet_name].freeze_panes(1, 0)

    # Build mapping info safely
    unique_all = agg.loc[agg["RemarkCombo"] == combo, "Account"].nunique() if not agg.empty else 0
    unique_included = agg_cat.loc[agg_cat["RemarkCombo"] == combo, "Account"].nunique() if not agg_cat.empty else 0
    unique_excluded = agg.loc[(agg["RemarkCombo"] == combo) & mask_exclude, "Account"].nunique() if not agg.empty else 0
    nts_in_combo = agg_cat.loc[(agg_cat["RemarkCombo"] == combo) & agg_cat["is_nts"], "Account"].nunique() if not agg_cat.empty else 0

    combo_map.append({
        "Combo_Sheet": sheet_name,
        "RemarkCombo": str(combo),
        "Unique_Accounts_All": int(unique_all),
        "Unique_Accounts_IncludedForCategorization": int(unique_included),
        "Unique_Accounts_Excluded": int(unique_excluded),
        "NTS_Accounts_in_Combo": int(nts_in_combo)
    })

# -----------------------
# Combo_Index sheet
# -----------------------
combo_df = pd.DataFrame(combo_map)
if combo_df.empty:
    combo_df = pd.DataFrame(columns=[
        "Combo_Sheet", "RemarkCombo", "Unique_Accounts_All",
        "Unique_Accounts_IncludedForCategorization",
        "Unique_Accounts_Excluded", "NTS_Accounts_in_Combo"
    ])
combo_df.to_excel(writer, sheet_name="Combo_Index", index=False)
autofit_columns(writer, combo_df, "Combo_Index")
writer.sheets["Combo_Index"].freeze_panes(1, 0)