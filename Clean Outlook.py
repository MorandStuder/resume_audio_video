# Correct the datetime usage

from datetime import datetime, timedelta, timezone

import win32com.client

# naive_datetime = datetime.now()  # offset-naive datetime
# aware_datetime = naive_datetime.replace(tzinfo=timezone.utc)  # now it's offset-aware

aware_datetime = datetime.now(timezone.utc)  # offset-aware datetime
naive_datetime = aware_datetime.replace(tzinfo=None)  # now it's offset-naive


# Function to remove large attachments
def remove_large_attachments(folder, size_limit, date_limit):
    items = folder.Items
    items.Sort("[ReceivedTime]", True)

    for item in range(items.Count, items.Count - 10, -1):
        try:
            message = items[item]
            for attachment in message.Attachments:
                print(message.ReceivedTime, message.Subject, attachment.Size)
            if message.ReceivedTime < date_limit:
                for attachment in message.Attachments:
                    if attachment.Size > size_limit:
                        print(
                            f"Removing attachment {attachment.FileName} from: {message.Subject}"
                        )
                        # Note: Direct deletion of attachments might not be possible due to Outlook security
                        # You may need to save the email after removing attachments
        except Exception as e:
            print(f"Error processing message: {e}")


# Connect to Outlook
outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

# Define the inbox folder
inbox = outlook.GetDefaultFolder(6)  # 6 refers to the inbox

# Define size limit (20 MB) and date limit (10 years ago)
size_limit = 20 * 1024 * 1024  # 20 MB
date_limit = datetime.now() - timedelta(days=10 * 365)
date_limit = date_limit.replace(tzinfo=timezone.utc)
print("date limite = ", date_limit)


items = inbox.Items
print("Nb msg =", items.Count)

test = 10844
for item in range(test, test + 10):
    message = items[item]
    print(item, message.ReceivedTime, message.Subject)
    for attachment in message.Attachments:
        print(attachment.Size)


# Clean the inbox
# remove_large_attachments(inbox, size_limit, date_limit)
