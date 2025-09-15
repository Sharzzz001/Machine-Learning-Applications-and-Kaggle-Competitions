import pandas as pd
import win32com.client as win32

# Example: load your dataframe (replace with your actual df)
df = pd.read_excel("escalation_input.xlsx")

# Ensure consistent casing for "Yes"/"No"
for col in ["Escalation RM", "Escalation TH", "Escalation GH"]:
    df[col] = df[col].astype(str).str.strip().str.upper()

# Initialize Outlook
outlook = win32.Dispatch('Outlook.Application')

# Group by account
for account, group in df.groupby("AccountNumber"):
    rm_email = group['RM'].iloc[0]  # single RM assumed per account
    to_address = rm_email

    cc_addresses = []
    if "YES" in group['Escalation TH'].values:
        cc_addresses.append(group['Team Head'].iloc[0])
    if "YES" in group['Escalation GH'].values:
        cc_addresses.append(group['Group Head'].iloc[0])

    # Build table for email body
    table_html = """
    <table border="1" cellspacing="0" cellpadding="3">
        <tr>
            <th>Account Number</th>
            <th>Request Type</th>
            <th>Document Name</th>
            <th>Due In (Days)</th>
        </tr>
    """
    for _, row in group.iterrows():
        table_html += f"""
        <tr>
            <td>{row['AccountNumber']}</td>
            <td>{row['Request Type']}</td>
            <td>{row['Document Name']}</td>
            <td>{row['Due In']}</td>
        </tr>
        """
    table_html += "</table>"

    # Build email body
    body = f"""
    <p>Dear {rm_email},</p>
    <p>The following account has outstanding document deficiencies:</p>
    {table_html}
    <p>Regards,<br>Onboarding Team</p>
    """

    # Create mail item
    mail = outlook.CreateItem(0)
    mail.Subject = f"Document Deficiency Escalation - Account {account}"
    mail.To = to_address
    mail.CC = ";".join(cc_addresses)
    mail.HTMLBody = body
    mail.Display()  # use .Send() to auto-send