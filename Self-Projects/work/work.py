import os
import zipfile

def extract_and_rename(zip_path, extraction_path, new_filename):
    # Step 1: Extract files from the zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Assume there is only one file in the zip file; get its name
        original_file_name = zip_ref.namelist()[0]
        zip_ref.extract(original_file_name, extraction_path)

    # Step 2: Rename the extracted file to the specified new filename
    original_file_path = os.path.join(extraction_path, original_file_name)
    new_file_path = os.path.join(extraction_path, new_filename)
    
    # Rename the file
    os.rename(original_file_path, new_file_path)

    # Step 3: Delete the zip file
    os.remove(zip_path)

# Example usage
zip_path = 'path/to/your/downloaded.zip'       # Path to the downloaded zip file
extraction_path = 'path/to/extracted/files/'   # Path to where files should be extracted
new_filename = 'master.xlsx'                   # Desired filename for the extracted file

extract_and_rename(zip_path, extraction_path, new_filename)