from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential

site_url = "https://yourcompany.sharepoint.com/sites/yoursite"
file_url = "/sites/yoursite/Shared Documents/yourfile.xlsx"
download_path = "yourfile.xlsx"

ctx = ClientContext(site_url).with_credentials(UserCredential("your.email@company.com", "yourpassword"))
with open(download_path, "wb") as f:
    response = ctx.web.get_file_by_server_relative_url(file_url).download(f).execute_query()

print(f"Downloaded to {download_path}")