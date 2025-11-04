for (account, request_type), group in df1.groupby(["AccountNumber", "RequestType"]):
    # --- Compare against email log (map RequestType -> ReviewType)
    already_logged = email_log[
        (email_log["AccountNumber"].astype(str) == str(account)) &
        (email_log["ReviewType"].astype(str) == str(request_type)) &
        (email_log["Rule"].isin(group["Rule"])) &
        (email_log["DocumentName"].isin(group["DocumentName"]))
    ]

    # Normalize dtype for merge
    for df_temp in [group, already_logged]:
        if df_temp["AccountNumber"].dtype != "O":
            df_temp.loc[:, "AccountNumber"] = df_temp["AccountNumber"].apply(
                lambda y: str(int(y)) if pd.notnull(y) else ""
            )

    match_columns = ["AccountNumber", "ReviewType", "DocumentName", "Rule"]

    merged = group.merge(
        already_logged,
        how='left',
        left_on=["AccountNumber", "RequestType", "DocumentName", "Rule"],
        right_on=match_columns,
        indicator=True
    )

    new_docs = merged[merged["_merge"] == "left_only"].drop(columns=["_merge"], errors="ignore")

    if new_docs.empty:
        logging.info(f"Skipping account {account} ({request_type}): already logged previously.")
        continue

    # --- Build full table (use unfiltered group for full picture)
    table_html = """
    <table border="1" cellspacing="0" cellpadding="3">
    <tr><th>Account Number</th><th>Request Type</th><th>Document Name</th>
    <th>Document Description</th><th>Overdue (Days)</th></tr>
    """
    for _, r in group.iterrows():
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

    # --- Create draft mail ---
    mail = outlook.CreateItem(0)
    mail.Subject = f"Document Deficiency (For Your Attention) - Account {account} ({request_type})"
    mail.To = clean_rm(group["RM"].iloc[0]) if "RM" in group.columns else None
    mail.CC = ";".join(cc_addresses) if cc_addresses else None
    mail.HTMLBody = body_template.replace("{{TABLE}}", table_html)
    mail.SentonBehalfOfName = "iwmkycops@nomura.com"
    mail.Save()

    logging.info(f"Draft created for account {account} ({request_type})")

    # --- Log only new docs ---
    for _, row in new_docs.iterrows():
        new_entry = {
            "AccountNumber": account,
            "ReviewType": request_type,      # <-- mapped here
            "DocumentName": row.get("DocumentName"),
            "Rule": row.get("Rule"),
            "EmailDate": datetime.now(),
            "To": mail.To,
            "CC": mail.CC,
            "Subject": mail.Subject,
            "Status": "Drafted"
        }
        email_log = pd.concat([email_log, pd.DataFrame([new_entry])], ignore_index=True)