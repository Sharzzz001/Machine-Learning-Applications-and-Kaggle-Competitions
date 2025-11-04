import win32com.client
import pythoncom
import os
import time
import logging

def refresh_excel_via_com(template_path, temp_save_path):
    """
    Replaces the VBS script: opens Excel workbook, refreshes data connections,
    saves to temp file, closes Excel.
    """
    logging.info(f"Refreshing Excel file via COM: {template_path}")
    pythoncom.CoInitialize()
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.DisplayAlerts = False
    excel.Visible = False

    try:
        wb = excel.Workbooks.Open(template_path)
        wb.RefreshAll()
        # give refresh time if data connections exist
        time.sleep(5)
        wb.SaveAs(temp_save_path)
        wb.Close(SaveChanges=False)
        logging.info(f"Excel refreshed and saved to {temp_save_path}")
    except Exception as e:
        logging.error(f"Excel COM refresh failed: {e}")
        raise
    finally:
        excel.Quit()
        pythoncom.CoUninitialize()
        
        
        
def run_refresh_and_rename():
    template_path = os.path.join(SAVE_FOLDER, "DocDeficiencyTemplate.xlsx")
    temp_path = os.path.join(SAVE_FOLDER, "DocDeficiencyTemplate - Temp.xlsx")
    refresh_excel_via_com(template_path, temp_path)

    if os.path.isfile(temp_path):
        os.rename(temp_path, OUTPUT_FILE)
        logging.info(f"Refreshed file saved as {OUTPUT_FILE}")
    else:
        raise FileNotFoundError(f"Temp file not found after refresh: {temp_path}")