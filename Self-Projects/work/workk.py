import os
import datetime
import win32com.client as win32

# === CONFIGURATION ===
iqy_path = r"C:\Path\To\Your\RR_Request.iqy"  # Path to the IQY file
save_folder = r"C:\Reports\RRRequest"
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
output_file = os.path.join(save_folder, f"RR_Request_{timestamp}.xlsx")

# === LAUNCH EXCEL AND OPEN IQY ===
excel = win32.gencache.EnsureDispatch('Excel.Application')
excel.Visible = False  # Set to True to watch it open
workbook = excel.Workbooks.Open(iqy_path)

# === REFRESH THE DATA CONNECTION ===
workbook.RefreshAll()

# === WAIT UNTIL REFRESH IS DONE ===
# Safer with DoEvents loop
while excel.CalculateUntilAsyncQueriesDone() != 0:
    pass

# === SAVE AS .XLSX AND CLOSE ===
workbook.SaveAs(output_file, FileFormat=51)  # 51 = .xlsx
workbook.Close(SaveChanges=False)
excel.Quit()

print(f"✅ SharePoint data saved to: {output_file}")