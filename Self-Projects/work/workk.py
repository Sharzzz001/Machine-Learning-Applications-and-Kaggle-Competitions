def draft_emails(df):
    logging.info("Drafting emails in Outlook (drafts only)...")
    outlook = win32.Dispatch("Outlook.Application")

    # Load email log
    if os.path.exists(EMAIL_LOG_FILE):
        email_log = pd.read_excel(EMAIL_LOG_FILE)
    else:
        email_log = pd.DataFrame(columns=[
            "AccountNumber", "ReviewType", "DocumentName", "Rule",
            "EmailDate", "To", "CC", "Subject", "Status"
        ])

    # Load escalation contact mapping (Sheet2)
    special_conditions = pd.read_excel(MAPPINGS_FILE, sheet_name="Sheet2")

    df1 = df[df["Matched"].astype(str).str.startswith("Yes")].copy()

    # === GROUP BY ACCOUNT ===
    for account, group in df1.groupby("AccountNumber"):
        # STEP 1: Identify new documents (not yet in log)
        already_logged = email_log[
            (email_log["AccountNumber"].astype(str) == str(account)) &
            (email_log["Rule"].isin(group["Rule"])) &
            (email_log["DocumentName"].isin(group["DocumentName"]))
        ]

        # Normalize datatypes for merge
        for x in [group, already_logged]:
            if x["AccountNumber"].dtype != "O":
                x["AccountNumber"] = x["AccountNumber"].apply(
                    lambda y: str(int(y)) if pd.notnull(y) else ""
                )

        match_columns = ["AccountNumber", "ReviewType", "DocumentName", "Rule"]

        merged = group.merge(
            already_logged,
            how="left",
            left_on=["AccountNumber", "RequestType", "DocumentName", "Rule"],
            right_on=match_columns,
            indicator=True
        )

        # Keep only new docs
        new_docs = merged[merged["_merge"] == "left_only"].drop(columns=["_merge"], errors="ignore")

        # STEP 2: If no new docs → skip
        if new_docs.empty:
            logging.info(f"Skipping account {account}: already logged previously.")
            continue

        # STEP 3: Build email table using full account info (complete view)
        account_full = df1[df1["AccountNumber"] == account]

        table_html = """
        <table border="1" cellspacing="0" cellpadding="3">
        <tr><th>Account Number</th><th>Request Type</th><th>Document Name</th>
        <th>Document Description</th><th>Overdue (Days)</th></tr>
        """
        for _, r in account_full.iterrows():
            table_html += f"""
            <tr>
                <td>{r.get('AccountNumber','')}</td>
                <td>{r.get('RequestType','')}</td>
                <td>{r.get('DocumentName','')}</td>
                <td>{r.get('DocDesc','')}</td>
                <td>{r.get('Due In (Days)','')}</td>
            </tr>
            """
        table_html += "</table>"

        # STEP 4: Recipients
        rm_email = group["RM"].iloc[0] if "RM" in group.columns else None
        to_address = clean_rm(rm_email)
        cc_addresses = []

        if "Yes" in group["Escalation TH"].values and pd.notnull(group["Team Head"].iloc[0]):
            cc_addresses.append(str(group["Team Head"].iloc[0]).strip())
        if "Yes" in group["Escalation GH"].values and pd.notnull(group["Group Head"].iloc[0]):
            cc_addresses.append(str(group["Group Head"].iloc[0]).strip())
        if "Yes" in group["Escalation FCC"].values and pd.notnull(special_conditions.iloc[0, 1]):
            cc_addresses.append(str(special_conditions.iloc[0, 1]).strip())
        if "Yes" in group["Escalation BM"].values and pd.notnull(special_conditions.iloc[1, 1]):
            cc_addresses.append(str(special_conditions.iloc[1, 1]).strip())

        cc_addresses = list(set(cc_addresses))  # dedupe

        # STEP 5: Draft one Outlook email per account
        body = f"""
        <p>Dear {rm_email or 'RM'},</p>
        <p>The following account has outstanding document deficiencies:</p>
        {table_html}
        <p>Please resolve the outstanding requirements as soon as possible,
        before consequential actions on the affected account take place.</p>
        <p>Thank You.<br><br>Regards,<br>CDD / IWM Operations CSG</p>
        """

        mail = outlook.CreateItem(0)
        mail.Subject = f"Document Deficiency (For Your Attention) - Account {account}"
        if to_address:
            mail.To = to_address
        if cc_addresses:
            mail.CC = ";".join(cc_addresses)
        mail.HTMLBody = body
        mail.SentonBehalfOfName = "iwmkycops@nomura.com"
        mail.Save()

        logging.info(f"Draft created for account {account} - To: {to_address} CC: {cc_addresses}")

        # STEP 6: Add only NEW document rows to email log
        for _, row in new_docs.iterrows():
            new_entry = {
                "AccountNumber": account,
                "ReviewType": row.get("RequestType"),
                "DocumentName": row.get("DocumentName"),
                "Rule": row.get("Rule"),
                "EmailDate": datetime.now(),
                "To": to_address,
                "CC": ";".join(cc_addresses),
                "Subject": mail.Subject,
                "Status": "Drafted"
            }
            email_log = pd.concat([email_log, pd.DataFrame([new_entry])], ignore_index=True)

        # Save updated log
        email_log.to_excel(EMAIL_LOG_FILE, index=False)