import requests
from requests_ntlm import HttpNtlmAuth

site_url = "https://yourcompany.sharepoint.com/sites/YourSite"
list_name = "YourListName"

url = f"{site_url}/_api/web/lists/getbytitle('{list_name}')/items?$expand=AttachmentFiles"

session = requests.Session()
session.auth = HttpNtlmAuth('DOMAIN\\username', 'password')

headers = {
    "Accept": "application/json;odata=verbose"
}

response = session.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    for item in data['d']['results']:
        for file in item['AttachmentFiles']['results']:
            print(f"File Name: {file['FileName']}")
            print(f"File URL: {file['ServerRelativeUrl']}")
else:
    print(f"Failed: {response.status_code}")