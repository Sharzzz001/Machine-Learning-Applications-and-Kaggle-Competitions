import os
import pandas as pd
import datetime
import win32com.client

outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

inbox = outlook.GetDefaultFolder(6)  

output_folder = r"C:\Path\To\Save\Attachments"  
start_date = datetime.datetime(2024, 1, 1)  
end_date = datetime.datetime(2024, 10, 31)  

data = []

messages = inbox.Items
messages = messages.Restrict("[ReceivedTime] >= '" + start_date.strftime('%m/%d/%Y') + "' AND [ReceivedTime] <= '" + end_date.strftime('%m/%d/%Y') + "'")

for message in messages:
    try:

        if message.Subject.startswith("Re:"):
            continue

        if "FI Blot" in message.Subject and ("AM" in message.Subject or "PM" in message.Subject):

            if message.Attachments:
                for attachment in message.Attachments:
                    attachment_path = os.path.join(output_folder, attachment.FileName)
                    attachment.SaveAsFile(attachment_path)

            data.append({
                "Subject": message.Subject,
                "ReceivedTime": message.ReceivedTime.strftime("%Y-%m-%d %H:%M:%S")
            })
    except Exception as e:
        print(f"Error processing email: {e}")

df = pd.DataFrame(data)

df.to_csv("email_log.csv", index=False)

print("Processed Emails:")
print(df)
