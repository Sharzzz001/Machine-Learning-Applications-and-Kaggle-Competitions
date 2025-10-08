import win32com.client as win32

# Init Outlook
outlook = win32.Dispatch("Outlook.Application")

# Your target account (can use DisplayName or SMTP address)
target_account = "other.account@yourbank.com"

def assign_account(mail, outlook, target_account):
    """
    Set the email to use a specific Outlook account instead of default.
    """
    for account in outlook.Session.Accounts:
        if account.SmtpAddress.lower() == target_account.lower() or account.DisplayName.lower() == target_account.lower():
            mail._oleobj_.Invoke(*(64209, 0, 8, 0, account))  # 64209 = SendUsingAccount
            return True
    return False
    
    
mail = outlook.CreateItem(0)
mail.Subject = f"Escalation for Account {account}"
mail.To = rm_email
mail.CC = ";".join(cc_addresses)
mail.Body = "This is a test email."

# Force it to use the other account
if not assign_account(mail, outlook, target_account):
    print(f"⚠️ Could not find account {target_account}, using default instead.")

mail.Save()  # saves into Drafts of that account