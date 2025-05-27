import datetime

import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

# Configuration
client_id = "morand.studer@eleven-strategy.co"
client_secret = "cNBSyY3bBLKusz"
tenant_id = "YOUR_TENANT_ID"
attachment_size_limit = 10 * 1024 * 1024  # Size in bytes (e.g., 10MB)
years_old = 2
scope = ["https://graph.microsoft.com/.default"]

# OAuth2 Client Setup
client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)
token = oauth.fetch_token(
    token_url=f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
    client_id=client_id,
    client_secret=client_secret,
    scope=scope,
)

# Set up headers for authorization
headers = {
    "Authorization": "Bearer " + token["access_token"],
    "Content-Type": "application/json",
}

# Calculate the date for the age filter
age_limit_date = (
    datetime.datetime.now() - datetime.timedelta(days=years_old * 365)
).isoformat()

# Request to get emails
url = f"https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?$filter=receivedDateTime lt {age_limit_date}&$select=id,subject"
response = requests.get(url, headers=headers)
emails = response.json().get("value", [])

# Process each email
for email in emails:
    # Get attachments for each email
    attachment_url = (
        f"https://graph.microsoft.com/v1.0/me/messages/{email['id']}/attachments"
    )
    attachments = requests.get(attachment_url, headers=headers).json().get("value", [])

    # Check each attachment's size and delete if necessary
    for attachment in attachments:
        if attachment["size"] > attachment_size_limit:
            print(
                f"Deleting attachment: {attachment['name']} from email: {email['subject']}"
            )
            del_url = f"https://graph.microsoft.com/v1.0/me/messages/{email['id']}/attachments/{attachment['id']}"
            del_response = requests.delete(del_url, headers=headers)
            if del_response.status_code == 204:
                print("Attachment deleted successfully.")
            else:
                print(f"Failed to delete attachment: {del_response.text}")

print("Finished processing emails.")
