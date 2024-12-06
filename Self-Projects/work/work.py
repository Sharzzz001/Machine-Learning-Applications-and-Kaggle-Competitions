def delete_all_csv_files(folder_path):
    """
    Deletes all CSV files in the specified folder.

    Parameters:
        folder_path (str): Path to the folder where CSV files should be deleted.
    """
    # Get all CSV files in the folder
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    
    # Check if there are any files to delete
    if not csv_files:
        print("No CSV files found in the folder.")
        return
    
    # Delete each file
    for file_path in csv_files:
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")
    
    print("All CSV files have been deleted.")

# Example usage
delete_all_csv_files(r"C:\Users\YourUsername\FolderWithCSVFiles")
