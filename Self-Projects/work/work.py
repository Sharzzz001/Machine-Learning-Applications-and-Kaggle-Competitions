import win32com.client
import pandas as pd

# Connect to Outlook
outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

# Access the inbox folder
inbox = outlook.GetDefaultFolder(6)  # 6 refers to the Inbox folder

# Retrieve all emails
messages = inbox.Items
messages = messages.Restrict("[MessageClass]='IPM.Note'")  # Filter standard emails

# List to store email data
email_data = []

# Loop through emails
for message in messages:
    try:
        subject = message.Subject
        received_time = message.ReceivedTime
        sender = message.SenderName
        
        email_data.append({"Subject": subject, "Received Time": received_time, "From": sender})
    except Exception as e:
        print(f"Error reading an email: {e}")

# Convert email data to a DataFrame
df = pd.DataFrame(email_data)

# Display the DataFrame
print(df)

# Save to a CSV file if needed
df.to_csv("emails.csv", index=False)