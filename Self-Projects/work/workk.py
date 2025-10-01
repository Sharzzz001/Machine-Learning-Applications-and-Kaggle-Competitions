import pandas as pd
import numpy as np
import re
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

# Example: assuming df already processed with account_no, remark_combo, Keyword
# And pivot_table already created
pivot_table = pd.pivot_table(
    df,
    index="Keyword",
    columns="remark_combo",
    values="account_no",
    aggfunc="count",
    fill_value=0,
)

# Prepare summary lines
total_unique_accounts = df["account_no"].nunique()
total_reasons = pivot_table.values.sum()

# --- Unique account level remark_combo distribution ---
# For each account, collapse into one remark_combo (same as you used earlier for remark_combos)
remark_combos = (
    df.groupby("account_no")["remark_combo"]
    .unique()
    .apply(lambda x: ", ".join(sorted(x)))
    .reset_index(name="remark_combo")
)

remark_combo_dist = remark_combos["remark_combo"].value_counts().reset_index()
remark_combo_dist.columns = ["Remark Combo", "Unique Account Count"]

# Save to Excel
output_file = "blocked_accounts_report.xlsx"
with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    pivot_table.to_excel(writer, sheet_name="Pivot")

    # Access sheet to append lines
    workbook = writer.book
    sheet = writer.sheets["Pivot"]

    # Find last row after pivot
    startrow = pivot_table.shape[0] + 3  # leave 2 blank rows

    # Write manual summary lines
    sheet.cell(row=startrow, column=1, value="Total unique accounts")
    sheet.cell(row=startrow, column=2, value=total_unique_accounts)

    sheet.cell(row=startrow + 1, column=1, value="Total reasons for blocked accounts")
    sheet.cell(row=startrow + 1, column=2, value=total_reasons)

    # Leave one blank line
    dist_start = startrow + 3
    sheet.cell(row=dist_start, column=1, value="Remark Combo Distribution (Unique Accounts)")

    # Write remark combo distribution below
    for i, row in remark_combo_dist.iterrows():
        sheet.cell(row=dist_start + i + 1, column=1, value=row["Remark Combo"])
        sheet.cell(row=dist_start + i + 1, column=2, value=row["Unique Account Count"])

# --- Auto-fit columns ---
wb = load_workbook(output_file)
ws = wb["Pivot"]

for col in ws.columns:
    max_length = 0
    col_letter = get_column_letter(col[0].column)
    for cell in col:
        try:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        except:
            pass
    ws.column_dimensions[col_letter].width = max_length + 2

wb.save(output_file)