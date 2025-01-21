import os
import pandas as pd
from tkinter import Tk, filedialog
from datetime import datetime

def process_excel_files():
    # Open file picker dialog
    root = Tk()
    root.withdraw()  # Hide the main Tkinter window
    file_paths = filedialog.askopenfilenames(
        title="Select Excel Files",
        filetypes=[("Excel Files", "*.xlsx")]
    )
    
    if not file_paths:
        print("No files selected.")
        return
    
    # Initialize data storage for the summary
    sheet1_data = []
    sheet2_data = []

    # Process each selected file
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        date = file_name[:11]  # Extract date from file name
        
        try:
            # Read Excel file
            excel_data = pd.ExcelFile(file_path)
            
            for sheet_name, storage in [("Sheet1", sheet1_data), ("Sheet2", sheet2_data)]:
                if sheet_name in excel_data.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Count blank comments and get unique owners
                    blank_comments = df['Comment'].isna().sum()
                    unique_owners = df['Owner'].dropna().unique()
                    
                    # Add data to the summary
                    storage.append({
                        "Date": date,
                        "Total Users": len(unique_owners),
                        "Blank Comments": blank_comments
                    })
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
    
    # Create summary DataFrames
    sheet1_summary = pd.DataFrame(sheet1_data)
    sheet2_summary = pd.DataFrame(sheet2_data)

    # Save summary to an output Excel file
    output_file = "Summary_Output.xlsx"
    with pd.ExcelWriter(output_file) as writer:
        sheet1_summary.to_excel(writer, index=False, sheet_name="Sheet1 Summary")
        sheet2_summary.to_excel(writer, index=False, sheet_name="Sheet2 Summary")

    print(f"Summary saved to {output_file}")

# Call the function to execute the workflow
process_excel_files()
