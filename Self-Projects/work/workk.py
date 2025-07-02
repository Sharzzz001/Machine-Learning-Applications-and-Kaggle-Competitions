import os
import datetime
import time
import win32com.client as win32

# === CONFIGURATION ===
iqy_path = r"C:\Path\To\Your\RR_Request.iqy"
save_folder = r"C:\Reports\RRRequest"
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
output_file = os.path.join(save_folder, f"RR_Request_{timestamp}.xlsx")

# === LAUNCH EXCEL AND OPEN IQY FILE ===
excel = win32.gencache.EnsureDispatch("Excel.Application")
excel.Visible = False
wb = excel.Workbooks.Open(iqy_path)

# === REFRESH ALL QUERYTABLES ===
for sheet in wb.Sheets:
    for qt in sheet.QueryTables:
        qt.Refresh(False)

# === WAIT (SAFELY) FOR DATA TO LOAD ===
time.sleep(10)  # Safe delay; adjust if needed

# === SAVE TO .XLSX ===
wb.SaveAs(output_file, FileFormat=51)  # 51 = .xlsx
wb.Close(SaveChanges=False)
excel.Quit()

print(f"✅ SharePoint data saved to: {output_file}")