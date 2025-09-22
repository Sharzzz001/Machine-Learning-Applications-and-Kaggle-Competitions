import os
import pandas as pd
from datetime import datetime
import win32com.client as win32

def draft_emails(df, log_file="Email_Log.xlsx"):
    outlook = win32.Dispatch("Outlook.Application")

    # Load or initialize log
    if os.path.exists(log_file):
        email_log = pd.read_excel(log_file)
    else:
        email_log = pd.DataFrame(columns=[
            "AccountNumber", "ReviewType", "DocumentName",
            "Rule", "EmailDate", "To", "CC", "Subject", "Status"
        ])

    # Group by account number (one email per account)
    for account, group in df.groupby("AccountNumber"):
        rm_email = str(group["RM"].iloc[0]) if pd.notna(group["RM"].iloc[0]) else ""
        th_name = str(group["Team Head"].iloc[0]) if pd.notna(group["Team Head"].iloc[0]) else ""
        gh_name = str(group["Group Head"].iloc[0]) if pd.notna(group["Group Head"].iloc[0]) else ""

        # Build CC list only if escalation flags are Yes
        cc_list = []
        if (group["Escalation TH"] == "Yes").any() and th_name:
            cc_list.append(th_name)
        if (group["Escalation GH"] == "Yes").any() and gh_name:
            cc_list.append(gh_name)

        # Deduplicate names in CC
        cc_list = list(set([c for c in cc_list if c]))
        cc_str = ";".join(cc_list)

        # Loop through all rows (documents) for this account
        for _, row in group.iterrows():
            review_type = row["Request Type"]
            doc_name = row["Document Name"]
            due_in = row["Due In"]
            rule = row["Rule"]

            # Check if already logged
            already_logged = (
                (email_log["AccountNumber"] == account) &
                (email_log["ReviewType"] == review_type) &
                (email_log["DocumentName"] == doc_name) &
                (email_log["Rule"] == rule)
            ).any()

            if already_logged:
                continue  # skip, already drafted

            # Create email draft
            mail = outlook.CreateItem(0)
            mail.Subject = f"Escalation: {account} - {review_type} - {doc_name} (Rule {rule})"
            mail.To = rm_email
            mail.CC = cc_str

            body = f"""
Hello,

The following account has a document deficiency:

Account Number: {account}
Request Type: {review_type}
Document: {doc_name}
Due In: {due_in} days

Regards,
Ops Team
"""
            mail.Body = body.strip()
            mail.Save()  # Save to Drafts

            # Log it
            new_entry = pd.DataFrame([{
                "AccountNumber": account,
                "ReviewType": review_type,
                "DocumentName": doc_name,
                "Rule": rule,
                "EmailDate": datetime.now(),
                "To": rm_email,
                "CC": cc_str,
                "Subject": mail.Subject,
                "Status": "Drafted"
            }])
            email_log = pd.concat([email_log, new_entry], ignore_index=True)

    # Save log back
    email_log.to_excel(log_file, index=False)