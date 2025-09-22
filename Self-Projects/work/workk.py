log_file = "Email_Log.xlsx"

if os.path.exists(log_file):
    email_log = pd.read_excel(log_file)
else:
    email_log = pd.DataFrame(columns=[
        "AccountNumber", "ReviewType", "DocumentName",
        "Rule", "EmailDate", "To", "CC", "Subject"
    ])

account = group['AccountNumber'].iloc[0]
review_type = group['Request Type'].iloc[0]
doc_name = group['Document Name'].iloc[0]
rule = group['Rule'].iloc[0]

# Check if this combination already logged
already_logged = (
    (email_log["AccountNumber"] == account) &
    (email_log["ReviewType"] == review_type) &
    (email_log["DocumentName"] == doc_name) &
    (email_log["Rule"] == rule)
).any()

if not already_logged:
    mail = outlook.CreateItem(0)
    mail.Subject = f"Escalation: {account} - {review_type} - {doc_name} (Rule {rule})"
    mail.To = rm_email
    mail.CC = ";".join(cc_addresses)
    mail.Body = f"This account has a document deficiency.\n\n"
    mail.Save()

    new_entry = pd.DataFrame([{
        "AccountNumber": account,
        "ReviewType": review_type,
        "DocumentName": doc_name,
        "Rule": rule,
        "EmailDate": datetime.now(),
        "To": rm_email,
        "CC": ";".join(cc_addresses),
        "Subject": mail.Subject
    }])
    email_log = pd.concat([email_log, new_entry], ignore_index=True)

email_log.to_excel(log_file, index=False)