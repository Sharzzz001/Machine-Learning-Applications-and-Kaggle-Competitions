import win32com.client as win32

outlook = win32.Dispatch("Outlook.Application")

print("📧 Accounts in this Outlook profile:")
for account in outlook.Session.Accounts:
    try:
        print(f"Display Name: {account.DisplayName} | SMTP: {account.SmtpAddress}")
    except Exception as e:
        print(f"Could not get SMTP for {account.DisplayName} - {e}")