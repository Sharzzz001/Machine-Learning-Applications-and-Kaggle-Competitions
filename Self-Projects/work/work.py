import os

def replace_january_with_jan(folder_path):
    try:
        # List all files in the folder
        for file_name in os.listdir(folder_path):
            # Check if "January" exists in the file name
            if "January" in file_name:
                # Create the new file name
                new_file_name = file_name.replace("January", "Jan")
                
                # Get full paths
                old_file_path = os.path.join(folder_path, file_name)
                new_file_path = os.path.join(folder_path, new_file_name)
                
                # Rename the file
                os.rename(old_file_path, new_file_path)
                print(f'Renamed: "{file_name}" -> "{new_file_name}"')
    except Exception as e:
        print(f"Error: {e}")

# Specify the folder path
folder_path = r"C:\path\to\your\folder"

# Call the function
replace_january_with_jan(folder_path)