import os
import datetime
import time
import win32com.client as win32

# === CONFIGURATION ===
iqy_path = r"C:\Path\To\Your\RR_Request.iqy"  # Path to the IQY file
save_folder = r"C:\Reports\RRRequest"
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
output_file = os.path.join(save_folder, f"RR_Request_{timestamp}.xlsx")

# === LAUNCH EXCEL AND OPEN IQY ===
excel = win32.gencache.EnsureDispatch('Excel.Application')
excel.Visible = False  # Change to True if you want to observe
workbook = excel.Workbooks.Open(iqy_path)

# === REFRESH ALL CONNECTIONS ===
workbook.RefreshAll()

# === WAIT FOR CONNECTIONS TO FINISH REFRESHING ===
max_wait_time = 60  # seconds
check_interval = 2  # seconds
elapsed = 0

while any(conn.Refreshing for conn in workbook.Connections) and elapsed < max_wait_time:
    time.sleep(check_interval)
    elapsed += check_interval

if elapsed >= max_wait_time:
    print("⚠️ Timed out waiting for refresh to complete.")

# === SAVE AS .XLSX AND CLOSE ===
workbook.SaveAs(output_file, FileFormat=51)  # 51 = .xlsx
workbook.Close(SaveChanges=False)
excel.Quit()

print(f"✅ SharePoint data saved to: {output_file}")