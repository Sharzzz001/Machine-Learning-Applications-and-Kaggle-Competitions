import requests
from requests_ntlm import HttpNtlmAuth

# === CONFIGURE THESE ===
sharepoint_url = "https://yourcompany.sharepoint.com/sites/yoursite/Shared%20Documents/yourfile.xlsx"
username = "DOMAIN\\your_username"   # Include domain if required, like "COMPANY\\john.doe"
password = "your_password"
local_filename = "downloaded_file.xlsx"  # or .csv etc.

# === DOWNLOAD FILE ===
response = requests.get(sharepoint_url, auth=HttpNtlmAuth(username, password), stream=True)

if response.status_code == 200:
    with open(local_filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"File downloaded successfully to: {local_filename}")
else:
    print(f"Failed to download file. Status Code: {response.status_code}")
    print(response.text)