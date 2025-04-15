import datetime

from O365 import Account, FileSystemTokenBackend

# Configuration
client_id = "morand.studer@eleven-strategy.com"
client_secret = "cNBSyY3bBLKusz"
attachment_size_limit = 10 * 1024 * 1024  # Size in bytes (e.g., 10MB)
years_old = 10
mailbox_name = "Inbox"  # e.g., 'Inbox'

# Setting up authentication
token_backend = FileSystemTokenBackend(token_path=".", token_filename="o365_token.txt")
account = Account((client_id, client_secret), token_backend=token_backend)

# Check if we are logged in
if not account.is_authenticated:
    # This will open a browser window for the authentication process
    account.authenticate(scopes=["basic", "message_all"])

# Accessing the mailbox
mailbox = account.mailbox(mailbox_name)
inbox = mailbox.inbox_folder()

# Calculate the date for the age filter
age_limit_date = datetime.datetime.now() - datetime.timedelta(days=years_old * 365)

# Searching for emails older than the specified number of years
messages = inbox.get_messages(
    limit=None,
    query=inbox.new_query().on_attribute("receivedDateTime").older_than(age_limit_date),
)
print(messages.Count)

# Processing emails
for message in messages:
    print(messages.Object)
    for attachment in message.attachments:
        print(attachment.size)

        # if attachment.size > attachment_size_limit:
        #     print(
        #         f"Deleting attachment: {attachment.name} from email: {message.subject}"
        #     )
        #     attachment.delete()

print("Finished processing emails.")
