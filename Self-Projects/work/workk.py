import requests
from requests_ntlm import HttpNtlmAuth
import pandas as pd
import datetime

# === CONFIGURATION ===
site_url = "https://sharepoint.company.com"
list_title = "RR Request V3"  # Must match exact SharePoint list name
username = "DOMAIN\\your_username"  # Example: "COMPANY\\john.doe"
password = "your_password"
output_folder = "C:\\Reports\\RRRequest"  # Set to your desired folder
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
output_file = f"{output_folder}\\RR_Request_Export_{timestamp}.xlsx"

# === SharePoint REST API endpoint ===
endpoint = f"{site_url}/teams/corp/opsacs/cob/_api/web/lists/getbytitle('{list_title}')/items"

# === Set headers ===
headers = {
    "Accept": "application/json;odata=verbose"
}

# === Send request ===
print("Downloading SharePoint list...")
response = requests.get(endpoint, auth=HttpNtlmAuth(username, password), headers=headers)

if response.status_code == 200:
    items = response.json()['d']['results']
    df = pd.json_normalize(items)
    df.to_excel(output_file, index=False)
    print(f"✅ Exported SharePoint list to: {output_file}")
else:
    print(f"❌ Failed to download. Status Code: {response.status_code}")
    print(response.text)