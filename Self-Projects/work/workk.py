import os
import datetime
import win32com.client as win32
import time

# === CONFIGURATION ===
template_path = r"C:\Reports\Templates\RR_Request_Template.xlsx"
save_folder = r"C:\Reports\RRRequest"
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
output_file = os.path.join(save_folder, f"RR_Request_{timestamp}.xlsx")

# === LAUNCH EXCEL AND OPEN TEMPLATE ===
excel = win32.DispatchEx("Excel.Application")  # DispatchEx = isolated session
excel.Visible = False
wb = excel.Workbooks.Open(template_path)

# === REFRESH QUERYTABLES ===
for sheet in wb.Sheets:
    for qt in sheet.QueryTables:
        qt.Refresh(False)
        while qt.Refreshing:
            time.sleep(1)

# === SAVE AND CLOSE ===
wb.SaveAs(output_file, FileFormat=51)  # 51 = .xlsx
wb.Close(SaveChanges=False)
excel.Quit()

print(f"✅ Exported to {output_file}")