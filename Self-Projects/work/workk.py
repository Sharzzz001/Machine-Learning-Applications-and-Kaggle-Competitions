import requests
from requests_ntlm import HttpNtlmAuth

# File URL - must be the **direct download link** (ends with ?download=1 or similar)
file_url = "https://yourcompany.sharepoint.com/sites/YourSite/Shared%20Documents/filename.xlsx"

# Destination path to save the file
save_path = r"C:\Users\YourName\Downloads\filename.xlsx"

# Use current Windows username and password via NTLM SSO
import getpass
username = os.getlogin()
domain = "YOURDOMAIN"  # Example: CORP or COMPANYAD

session = requests.Session()
session.auth = HttpNtlmAuth(f"{domain}\\{username}", getpass.getpass("Windows Password (SSO): "))

# Download the file
response = session.get(file_url)

if response.status_code == 200:
    with open(save_path, 'wb') as f:
        f.write(response.content)
    print("File downloaded successfully.")
else:
    print(f"Failed to download. Status code: {response.status_code}")