folder_path = r"C:\path\to\your\snapshot\folder"
db_path = r"C:\path\to\RR_Request_DB.accdb"

if merge_snapshots_to_access(folder_path, db_path):
    print("✔ Access DB updated with new files. Ready to calculate aging.")
else:
    print("🔁 No new files to import. Aging calculation not required.")