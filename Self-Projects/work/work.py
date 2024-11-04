import os
import zipfile
import glob

def extract_and_rename_latest_zip(download_directory, extraction_path, new_filename):
    # Step 1: Find the latest zip file in the specified directory
    zip_files = glob.glob(os.path.join(download_directory, '*.zip'))
    if not zip_files:
        print("No zip files found in the directory.")
        return
    
    latest_zip_file = max(zip_files, key=os.path.getctime)

    # Step 2: Extract files from the latest zip file
    with zipfile.ZipFile(latest_zip_file, 'r') as zip_ref:
        # Assume there is only one file in the zip file; get its name
        original_file_name = zip_ref.namelist()[0]
        zip_ref.extract(original_file_name, extraction_path)

    # Step 3: Rename the extracted file to the specified new filename
    original_file_path = os.path.join(extraction_path, original_file_name)
    new_file_path = os.path.join(extraction_path, new_filename)
    
    # Rename the file
    os.rename(original_file_path, new_file_path)

    # Step 4: Delete the original zip file
    os.remove(latest_zip_file)

# Example usage
download_directory = 'path/to/download/directory'  # Directory where the zip file is downloaded
extraction_path = 'path/to/extracted/files/'       # Path to extract the file to
new_filename = 'master.xlsx'                       # Desired filename for the extracted file

extract_and_rename_latest_zip(download_directory, extraction_path, new_filename)