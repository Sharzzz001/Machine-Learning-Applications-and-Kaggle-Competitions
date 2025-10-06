# ---------- BUILD PIVOT ----------
pivot = (
    exploded.pivot_table(
        index="Category",
        columns="RemarkCombo_Clean",
        values="Account",
        aggfunc=lambda x: x.nunique(),
        fill_value=0,
    )
)

pivot["Total"] = pivot.sum(axis=1)

# --- 1) Get total unique accounts per combo (for "Total Volume" row)
remark_combo_totals = (
    exploded.groupby("RemarkCombo_Clean")["Account"]
    .nunique()
    .reindex(pivot.columns.drop("Total"), fill_value=0)
)
remark_combo_totals["Total"] = remark_combo_totals.sum()

# --- 2) Build formatted report pivot
report_rows = []

# First row: total volume per combo
row_total = ["Total Volume (Unique Accounts)"] + remark_combo_totals.tolist()
report_rows.append(row_total)

# Second row: Block Reasons (label row, blanks in numeric cols)
row_block = ["Block Reasons"] + [""] * len(remark_combo_totals)
report_rows.append(row_block)

# Remaining rows: actual pivot rows
for cat, row in pivot.iterrows():
    row_list = [cat] + row.tolist()
    report_rows.append(row_list)

# Final DataFrame
report_pivot = pd.DataFrame(
    report_rows,
    columns=["Block Code"] + remark_combo_totals.index.tolist()
)


report_pivot.to_excel(writer, sheet_name="Pivot_Overview", index=False, startrow=0)