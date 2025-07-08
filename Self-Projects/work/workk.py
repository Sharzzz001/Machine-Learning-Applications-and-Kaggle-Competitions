import win32com.client
import os

# === CONFIGURATION ===
access_path = r"C:\Path\To\Your\Database.accdb"      # Change this to your Access DB path
query_name = "YourQueryName"                         # Change this to the name of your saved query
export_path = r"C:\Path\To\Export\output.xlsx"       # Desired output path for Excel file

# Excel export needs to be .xlsx but Access natively saves as .xls
temp_export_path = export_path.replace('.xlsx', '.xls')  # Temporary .xls export

# === START AUTOMATION ===
access = win32com.client.Dispatch("Access.Application")
access.Visible = False

# Open the DB
access.OpenCurrentDatabase(access_path)

# Export the query result to Excel (.xls)
access.DoCmd.TransferSpreadsheet(
    TransferType=1,       # acExport
    SpreadsheetType=8,    # acSpreadsheetTypeExcel9 (.xls)
    TableName=query_name,
    FileName=temp_export_path,
    HasFieldNames=True
)

# Close Access
access.Quit()

# Optional: Convert .xls to .xlsx using Excel
excel = win32com.client.Dispatch("Excel.Application")
wb = excel.Workbooks.Open(temp_export_path)
wb.SaveAs(export_path, FileFormat=51)  # FileFormat=51 is .xlsx
wb.Close(False)
excel.Quit()

# Delete the temporary .xls file
os.remove(temp_export_path)

print(f"Exported '{query_name}' from Access to {export_path}")