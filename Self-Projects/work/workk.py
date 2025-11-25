import os
import warnings
from datetime import datetime

import pandas as pd
import win32com.client as win32
import logging


def draft_emails(df):
    logging.info("Drafting emails in Outlook (drafts only)...")
    outlook = win32.Dispatch("Outlook.Application")

    # --- Load email log ---
    if os.path.exists(EMAIL_LOG_FILE):
        email_log = pd.read_excel(EMAIL_LOG_FILE)
    else:
        email_log = pd.DataFrame(
            columns=[
                "AccountNumber",
                "ReviewType",
                "DocumentName",
                "Rule",
                "EmailDate",
                "To",
                "CC",
                "Subject",
                "Status",
                "Comments",  # user-editable comments column
            ]
        )

    # --- Load escalation contact mapping (Sheet2) ---
    special_conditions = pd.read_excel(MAPPINGS_FILE, sheet_name="Sheet2")

    # Only rows that actually matched a rule
    df1 = df[df["Matched"].astype(str).str.startswith("Yes")].copy()

    # --- Group by AccountNumber (as in your original function) ---
    for account, group in df1.groupby("AccountNumber"):
        # --- Find already logged entries for this account ---
        already_logged = email_log[
            (email_log["AccountNumber"].astype(str) == str(account))
            & (email_log["ReviewType"].isin(group["RequestType"]))
            & (email_log["Rule"].isin(group["Rule"]))
            & (email_log["DocumentName"].isin(group["DocumentName"]))
        ]

        # --- Normalize datatypes for merge (AccountNumber as string) ---
        for x in (group, already_logged):
            if "AccountNumber" in x.columns and x["AccountNumber"].dtype != "O":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=FutureWarning)
                    x.loc[:, "AccountNumber"] = x["AccountNumber"].apply(
                        lambda y: str(int(y)) if pd.notnull(y) else ""
                    )

        match_columns = ["AccountNumber", "ReviewType", "DocumentName", "Rule"]

        merged = group.merge(
            already_logged,
            how="left",
            left_on=["AccountNumber", "RequestType", "DocumentName", "Rule"],
            right_on=match_columns,
            indicator=True,
        )

        # --- Keep only new docs ---
        new_docs = merged[merged["_merge"] == "left_only"].drop(
            columns=["_merge"], errors="ignore"
        )

        if new_docs.empty:
            logging.info(f"Skipping account {account}: already logged previously.")
            continue

        # --- FULL ACCOUNT VIEW for tables (all rows for this account) ---
        account_full = df1[df1["AccountNumber"] == account].copy()

        # --------- SPLIT INTO TWO TABLES BASED ON DocumentName ----------

        # Treat NaN / empty / whitespace-only as "blank"
        docname_series = account_full.get("DocumentName", pd.Series(index=account_full.index))
        docname_str = docname_series.astype(str).str.strip()

        # Table 1: DocumentName NOT blank
        mask_doc = (docname_str != "") & (~docname_str.isna())
        table1_df = account_full[mask_doc].copy()

        # Table 2: DocumentName blank (NaN or empty)
        table2_df = account_full[~mask_doc].copy()

        # --- Helper to build HTML table or "Nothing to report" ---
        def build_table(d):
            if d.empty:
                return "<p>Nothing to report.</p>"

            html = """
<table border="1" cellspacing="0" cellpadding="3">
<tr>
  <th>Account Number</th>
  <th>Request Type</th>
  <th>Document Name</th>
  <th>Document Description</th>
  <th>Overdue (Days)</th>
</tr>
"""
            for _, r in d.iterrows():
                html += f"""
<tr>
  <td>{r.get('AccountNumber', '')}</td>
  <td>{r.get('RequestType', '')}</td>
  <td>{r.get('DocumentName', '')}</td>
  <td>{r.get('DocDesc', '')}</td>
  <td>{r.get('Due In (Days)', '')}</td>
</tr>
"""
            html += "</table>"
            return html

        table1_html = build_table(table1_df)
        table2_html = build_table(table2_df)

        # ------------------ RECIPIENTS (To / CC) ------------------
        rm_email = group["RM"].iloc[0] if "RM" in group.columns else None
        to_address = clean_rm(rm_email)

        cc_addresses = []

        if (
            "Escalation TH" in group.columns
            and "Team Head" in group.columns
            and "Yes" in group["Escalation TH"].values
            and pd.notnull(group["Team Head"].iloc[0])
        ):
            cc_addresses.append(str(group["Team Head"].iloc[0]).strip())

        if (
            "Escalation GH" in group.columns
            and "Group Head" in group.columns
            and "Yes" in group["Escalation GH"].values
            and pd.notnull(group["Group Head"].iloc[0])
        ):
            cc_addresses.append(str(group["Group Head"].iloc[0]).strip())

        # Special FCC / BM escalation emails from Sheet2
        # (assumes special_conditions has those emails in [0,1] and [1,1])
        if (
            "Escalation FCC" in group.columns
            and "Yes" in group["Escalation FCC"].values
            and pd.notnull(special_conditions.iloc[0, 1])
        ):
            cc_addresses.append(str(special_conditions.iloc[0, 1]).strip())

        if (
            "Escalation BM" in group.columns
            and "Yes" in group["Escalation BM"].values
            and pd.notnull(special_conditions.iloc[1, 1])
        ):
            cc_addresses.append(str(special_conditions.iloc[1, 1]).strip())

        cc_addresses = list(set(cc_addresses))  # dedupe

        # ------------------ BUILD EMAIL BODY (TWO TABLES) ------------------
        body = f"""
<p>Dear {rm_email or ''},</p>

<p>The following account has pending document deficiencies:</p>
{table1_html}

<p>The following account has pending AO Physical Documents:</p>
{table2_html}

<p>Please resolve the outstanding requirements as soon as possible, before consequential actions on the affected account takes place.</p>

<p>Thank You.<br><br>
Regards,<br>
CDD / IWM Operations CSG</p>
"""

        # ------------------ CREATE DRAFT EMAIL ------------------
        mail = outlook.CreateItem(0)  # MailItem
        mail.Subject = f"Document Deficiency (For Your Attention) - Account {account}"
        if to_address:
            mail.To = to_address
        if cc_addresses:
            mail.CC = ";".join(cc_addresses)
        mail.HTMLBody = body
        mail.SentonBehalfOfName = "iwmkycops@nomura.com"
        mail.Save()  # Draft only; no send, no timestamp logic

        logging.info(
            f"Draft created for account {account} - To: {to_address} CC: {cc_addresses}"
        )

        # ------------------ UPDATE EMAIL LOG (ONLY NEW DOCS) ------------------
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
                "Status": "Drafted",
                "Comments": "",  # user can fill manually later
            }
            email_log = pd.concat([email_log, pd.DataFrame([new_entry])], ignore_index=True)

        # Save updated log after each account
        email_log.to_excel(EMAIL_LOG_FILE, index=False)