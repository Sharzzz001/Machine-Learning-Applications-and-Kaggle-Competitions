# DocDeficiency_Automation_Full.py
# Single-file pipeline: VBS refresh -> transform -> protocol mapping -> RM enrichment -> draft emails
# Author: generated for you
# NOTE: edit the paths in CONFIG below before running.

import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, date
import pandas as pd
import win32com.client as win32
import logging
import sys

# -------------------------
# CONFIG - EDIT IF NEEDED
# -------------------------
SAVE_FOLDER = r'\\global.nomura.com\corp\EU\OPS\SVD_NSL\IWMPrivate\Doc Deficiency Sharepoint Daily Output'
CONFIG_FOLDER = r'C:\path\to\your\config'  # e.g. where mappings.xlsx, SCM.xlsx live
NOTEBOOK_PATH = None  # Not used here (we integrated notebook logic)
VBS_SCRIPT = os.path.join(SAVE_FOLDER, "script.vbs")
TEMPLATE_TEMP = os.path.join(SAVE_FOLDER, "DocDeficiencyTemplate - Temp.xlsx")

# Fixed config file paths (user said these are fixed)
MAPPINGS_FILE = os.path.join(CONFIG_FOLDER, "mappings.xlsx")   # your mapping config
RR_FILE = os.path.join(SAVE_FOLDER, "test_files", "RR_Request.xlsx")  # change if different
AO_FILE = os.path.join(CONFIG_FOLDER, "AOB Tracker V2.1.xlsx")
SCM_FILE = os.path.join(CONFIG_FOLDER, "SCM.xlsx")

# Email log single file (persistent)
EMAIL_LOG_FILE = os.path.join(SAVE_FOLDER, "Email_Log.xlsx")

# Today/time strings & datewise folder
TIMESTAMP = datetime.now().strftime("%Y-%m-%d")
DATE_FOLDER = os.path.join(SAVE_FOLDER, TIMESTAMP)
os.makedirs(DATE_FOLDER, exist_ok=True)

# Output filenames in date folder
OUTPUT_FILE = os.path.join(DATE_FOLDER, f"DocDeficiency-{TIMESTAMP}.xlsx")  # final refreshed file
FLAT_FILE = os.path.join(DATE_FOLDER, "flat.xlsx")
PROTOCOL_OUTPUT_FILE = os.path.join(DATE_FOLDER, "protocol_mapping_output_withRM.xlsx")

# Logging
LOG_FILE = os.path.join(SAVE_FOLDER, "automation_log.txt")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

# -------------------------
# Utility helpers
# -------------------------
def safe_read_excel(path, **kwargs):
    logging.info(f"Reading Excel: {path}")
    return pd.read_excel(path, **kwargs)

def run_vbs_and_rename():
    """
    Runs the VBS (which should Refresh & Save Temp), then renames the Temp to a timestamped output.
    """
    try:
        logging.info("Running VBS to refresh Excel...")
        subprocess.run(['cscript.exe', '//B', '//Nologo', VBS_SCRIPT], check=True)
        logging.info("VBS executed.")
    except Exception as e:
        logging.error(f"Failed to run VBS: {e}")
        raise

    if os.path.isfile(TEMPLATE_TEMP):
        logging.info(f"Found temp file {TEMPLATE_TEMP}. Renaming to {OUTPUT_FILE}")
        shutil.move(TEMPLATE_TEMP, OUTPUT_FILE)
    else:
        logging.error(f"Expected temp file not found at {TEMPLATE_TEMP}")
        raise FileNotFoundError(TEMPLATE_TEMP)

# -------------------------
# Transform (if you want to include your transform here)
# -------------------------
def transform_doc_deficiency(df):
    """
    Converts wide document columns (Document1..Document5) into flat rows.
    Expects the incoming df to resemble the flattened Excel produced by your VBS refresh.
    Column expectations (best-effort): Title (AccountNumber), Request Type, General Status,
      Doc Defic Start date 1, Document 1..5, Document Deficiency Type 1..5, Extended Deadline 1..5, Ext reason 1..5, etc.
    """
    # mapping of expected column names - adapt if your excel uses slightly different names
    # We will try to find common patterns; fallback to exact given names used previously
    col_map = {
        'AccountNumber': ['Title', 'AccountNumber'],
        'RequestType': ['Request Type', 'RequestType'],
        'GeneralStatus': ['General Status', 'GeneralStatus'],
        'DocDefiStartDate': ['Doc Defic Start date 1', 'DocDefiStartDate', 'DocDefiStartDate1'],
        'DateOfCompletion': ['Date of Completion', 'DateOfCompletion', 'DateOfCompletion1'],
        'Modified': ['Modified'],
        'Modified By': ['Modified By', 'ModifiedBy']
    }

    # helper to pick existing column name
    def pick(col_candidates):
        for c in col_candidates:
            if c in df.columns:
                return c
        return None

    acct_col = pick(col_map['AccountNumber'])
    req_col = pick(col_map['RequestType'])
    gen_col = pick(col_map['GeneralStatus'])
    start_col = pick(col_map['DocDefiStartDate'])
    # fallback: if no start col, try common names
    if start_col is None:
        start_col = [c for c in df.columns if 'start' in c.lower()]
        start_col = start_col[0] if start_col else None

    rows = []
    for _, r in df.iterrows():
        for i in range(1, 6):
            # attempt typical column names
            doc_name_col = next((c for c in df.columns if c.lower().strip() in [f"document {i}".lower(), f"document{i}".lower(), f"docname{i}".lower(), f"docname {i}".lower()]), None)
            doc_type_col = next((c for c in df.columns if c.lower().strip() in [f"document deficiency type {i}".lower(), f"doctype{i}".lower(), f"doc type{i}".lower(), f"doctype {i}".lower()]), None)
            doc_status_col = next((c for c in df.columns if c.lower().strip() in [f"document status {i}".lower(), f"docstatus{i}".lower(), f"doc status{i}".lower()]), None)
            ext_dead_col = next((c for c in df.columns if c.lower().strip() in [f"extended deadline {i}".lower(), f"extendeddeadline{i}".lower(), f"extendeddeadline {i}".lower()]), None)
            doc_desc_col = next((c for c in df.columns if c.lower().strip() in [f"document description {i}".lower(), f"docdesc{i}".lower(), f"docdesc {i}".lower(), f"docdesc{i}".lower()]), None)

            # If no doc name col found for this slot, skip
            if not doc_name_col:
                continue
            doc_name = r.get(doc_name_col)
            if pd.isna(doc_name):
                continue

            row_out = {
                'AccountNumber': r.get(acct_col) if acct_col else None,
                'RequestType': r.get(req_col) if req_col else None,
                'GeneralStatus': r.get(gen_col) if gen_col else None,
                'DocDefiStartDate': r.get(start_col) if start_col else None,
                'DateOfCompletion': r.get(start_col),  # fallback
                'Modified': r.get('Modified') if 'Modified' in df.columns else None,
                'ModifiedBy': r.get('Modified By') if 'Modified By' in df.columns else None,
                'DocumentName': doc_name,
                'DocDefiType': r.get(doc_type_col) if doc_type_col else None,
                'DocumentStatus': r.get(doc_status_col) if doc_status_col else None,
                'ExtendedDeadline': r.get(ext_dead_col) if ext_dead_col else None,
                'DocDesc': r.get(doc_desc_col) if doc_desc_col else None
            }
            rows.append(row_out)
    flat = pd.DataFrame(rows)
    return flat

# -------------------------
# Protocol Mapping Step
# -------------------------
def calculate_due_days(start_date):
    if pd.isna(start_date):
        return None
    try:
        due = pd.to_datetime(start_date, errors='coerce')
        if pd.isna(due):
            return None
        today = date.today()
        return (today - due.date()).days
    except Exception:
        return None

def protocol_mapping(flat_df, mapping_df):
    logging.info("Running protocol mapping...")
    # Clean columns
    df = flat_df.copy()
    # Filter empty/irrelevant
    if 'DocDefiType' in df.columns:
        df = df.dropna(subset=['DocDefiType'])
    if 'DocumentStatus' in df.columns:
        df = df[df['DocumentStatus'].astype(str).str.strip().str.upper() != 'COMPLETED']

    # dedupe
    dedupe_cols = []
    for c in ['AccountNumber', 'RequestType', 'DocumentName', 'DocDefiType']:
        if c in df.columns:
            dedupe_cols.append(c)
    if dedupe_cols:
        df = df.drop_duplicates(subset=dedupe_cols)

    # DueDays and FCC extension flag
    df['DueDays'] = df['DocDefiStartDate'].apply(calculate_due_days)
    df['FCC Extension Received'] = df['ExtendedDeadline'].apply(lambda x: 'Yes' if pd.notna(x) and str(x).strip() != '' else 'No')

    output_rows = []
    # Normalise mapping df columns (strip and upper where useful)
    mapping = mapping_df.copy()
    # Ensure int/float for DueInMin/Max if numeric, else try parse numbers - but mapping is expected clean
    # For each row in df, find matching entries in mapping
    for _, row in df.iterrows():
        due = row.get('DueDays')
        req = str(row.get('RequestType') or '').strip().upper()
        doc_type = str(row.get('DocDefiType') or '').strip().upper()
        fcc = str(row.get('FCC Extension Received') or '').strip().upper()

        # Attempt matching - mapping comparisons are case-insensitive. We rely on mapping_df having the columns:
        # Process Type, Doc Type, FCC Extension Received, DueInMin, DueInMax
        matched = mapping[
            (mapping['Process Type'].astype(str).str.strip().str.upper() == req) &
            (mapping['Doc Type'].astype(str).str.strip().str.upper() == doc_type)
        ].copy()

        # Filter FCC Extension Received: allow 'Any' or match value
        def fcc_filter(x):
            x = str(x).strip().upper()
            return (x == 'ANY') or (x == fcc)
        if not matched.empty:
            matched = matched[matched['FCC Extension Received'].apply(fcc_filter)]

        # Filter DueInMin/Max
        if 'DueInMin' in mapping.columns and 'DueInMax' in mapping.columns and not matched.empty:
            def due_in_range(row_map):
                try:
                    minv = float(row_map['DueInMin']) if pd.notna(row_map['DueInMin']) else float('-inf')
                except:
                    minv = float('-inf')
                try:
                    maxv = float(row_map['DueInMax']) if pd.notna(row_map['DueInMax']) else float('inf')
                except:
                    maxv = float('inf')
                if due is None:
                    return False
                return (due >= minv) and (due <= maxv)
            matched = matched[matched.apply(due_in_range, axis=1)]

        # Build outputs
        if matched.empty:
            out = row.to_dict()
            out['Matched'] = 'No'
            output_rows.append(out)
        else:
            # If multiple matches, mark as multiple and append copied info
            if len(matched) > 1:
                logging.warning(f"Multiple mapping matches for Account {row.get('AccountNumber')} / DocType {doc_type} / DueDays {due}")
                for _, m in matched.iterrows():
                    out = row.to_dict()
                    out['Matched'] = 'Yes (Multiple)'
                    # append mapping columns except the matching key columns we don't want to overwrite
                    for col in m.index:
                        if col not in ['Process Type', 'Doc Type', 'DueInMin', 'DueInMax', 'FCC Extension Received']:
                            out[col] = m[col]
                    output_rows.append(out)
            else:
                m = matched.iloc[0]
                out = row.to_dict()
                out['Matched'] = 'Yes'
                for col in m.index:
                    if col not in ['Process Type', 'Doc Type', 'DueInMin', 'DueInMax', 'FCC Extension Received']:
                        out[col] = m[col]
                output_rows.append(out)

    result = pd.DataFrame(output_rows)
    return result

# -------------------------
# RM enrichment & merges
# -------------------------
def enrich_with_rm(protocol_df):
    logging.info("Enriching with AO/RR/SCM data...")
    # Read supporting files
    rr = safe_read_excel(RR_FILE, usecols=None) if os.path.exists(RR_FILE) else pd.DataFrame()
    ao = safe_read_excel(AO_FILE, usecols=None) if os.path.exists(AO_FILE) else pd.DataFrame()
    scm = safe_read_excel(SCM_FILE, usecols=None) if os.path.exists(SCM_FILE) else pd.DataFrame()

    # canonical column names
    # rename some columns if possible
    if 'Request Title' in rr.columns and 'AccountNumber' not in rr.columns:
        rr = rr.rename(columns={'Request Title': 'AccountNumber'})
    if 'Account No' in ao.columns and 'AccountNumber' not in ao.columns:
        ao = ao.rename(columns={'Account No': 'AccountNumber'})

    # ensure string types for merge keys
    for df in [rr, ao, scm, protocol_df]:
        for c in ['AccountNumber', 'Sales Code']:
            if c in df.columns:
                df[c] = df[c].astype(str)

    # split into Account Opening & others
    df_main = protocol_df.copy()
    df_main['RequestType_norm'] = df_main['RequestType'].astype(str).str.upper()
    df_ao = df_main[df_main['RequestType_norm'] == 'ACCOUNT OPENING'].copy()
    df_rr = df_main[df_main['RequestType_norm'] != 'ACCOUNT OPENING'].copy()

    # merge
    if not ao.empty and 'AccountNumber' in ao.columns:
        df_ao = df_ao.merge(ao, how='left', on='AccountNumber', suffixes=('', '_ao'))
    if not rr.empty and 'AccountNumber' in rr.columns:
        df_rr = df_rr.merge(rr, how='left', on='AccountNumber', suffixes=('', '_rr'))

    combined = pd.concat([df_ao, df_rr], ignore_index=True, sort=False)

    # Finally merge SCM on Sales Code if available
    if not scm.empty and 'Sales Code' in scm.columns and 'Sales Code' in combined.columns:
        combined = combined.merge(scm, how='left', on='Sales Code', suffixes=('', '_scm'))
    elif not scm.empty and 'Sales Code' in scm.columns and 'Sales Code' in combined.columns:
        combined = combined.merge(scm, how='left', left_on='Sales Code', right_on='Sales Code')

    # cleanup helper columns
    if 'RequestType_norm' in combined.columns:
        combined = combined.drop(columns=['RequestType_norm'])

    return combined

# -------------------------
# Email drafting
# -------------------------
def clean_rm(rm_value):
    if pd.isna(rm_value):
        return None
    parts = [x.strip() for x in str(rm_value).split('/') if x.strip()]
    return ";".join(parts) if parts else None

def load_email_log():
    if os.path.exists(EMAIL_LOG_FILE):
        try:
            return pd.read_excel(EMAIL_LOG_FILE)
        except Exception:
            return pd.DataFrame(columns=["AccountNumber","ReviewType","DocumentName","Rule","EmailDate","To","CC","Subject","Status"])
    else:
        return pd.DataFrame(columns=["AccountNumber","ReviewType","DocumentName","Rule","EmailDate","To","CC","Subject","Status"])

def save_email_log(df):
    df.to_excel(EMAIL_LOG_FILE, index=False)

def draft_emails(output_df):
    logging.info("Drafting emails in Outlook (drafts only)...")
    outlook = win32.Dispatch("Outlook.Application")
    email_log = load_email_log()

    # only process matched rows
    df1 = output_df[output_df['Matched'].astype(str).str.startswith('Yes')].copy()
    if df1.empty:
        logging.info("No matched rows to email.")
        return

    # Group by account
    for account, group in df1.groupby('AccountNumber'):
        # get recipients
        rm_email = group.get('RM').iloc[0] if 'RM' in group.columns else None
        to_address = clean_rm(rm_email)
        cc_addresses = []
        if 'Escalation TH' in group.columns and group['Escalation TH'].astype(str).str.upper().str.contains('YES').any():
            th = group.get('Team Head').iloc[0] if 'Team Head' in group.columns else None
            if pd.notna(th):
                cc_addresses.append(str(th).strip())
        if 'Escalation GH' in group.columns and group['Escalation GH'].astype(str).str.upper().str.contains('YES').any():
            gh = group.get('Group Head').iloc[0] if 'Group Head' in group.columns else None
            if pd.notna(gh):
                cc_addresses.append(str(gh).strip())
        cc_addresses = [c for c in cc_addresses if c]

        # one email per account - include table of all rows in this group
        table_html = '<table border="1" cellspacing="0" cellpadding="3"><tr><th>Account Number</th><th>Request Type</th><th>Document Name</th><th>Document Description</th><th>Overdue (Days)</th></tr>'
        for _, r in group.iterrows():
            acct = r.get('AccountNumber', '')
            reqt = r.get('RequestType', '')
            docn = r.get('DocumentName', '')
            desc = r.get('DocDesc', '')
            due = r.get('DueDays', '')
            table_html += f"<tr><td>{acct}</td><td>{reqt}</td><td>{docn}</td><td>{desc}</td><td>{due}</td></tr>"
        table_html += "</table>"

        rm_addr_print = rm_email if rm_email else 'RM'

        body = f"""
        <p>Dear {rm_addr_print},</p>
        <p>The following account has outstanding document deficiencies:</p>
        {table_html}
        <p>Please resolve the outstanding requirements as soon as possible, before consequential actions on the affected account take place.</p>
        <p>Thank You.<br><br>Regards,<br>CDD / IWM Operations CSG</p>
        """

        # Create draft
        try:
            mail = outlook.CreateItem(0)  # 0=olMailItem
            mail.Subject = f"Document Deficiency Escalation (For Your Attention) - Account {account}"
            if to_address:
                mail.To = to_address
            if cc_addresses:
                mail.CC = ";".join(cc_addresses)
            mail.HTMLBody = body
            # send on behalf not required - just keep drafts
            mail.Save()  # saves draft in Outlook
            status = "Drafted"
            logging.info(f"Draft created for account {account} -> To: {to_address} CC: {cc_addresses}")
        except Exception as e:
            logging.error(f"Failed to create draft for {account}: {e}")
            status = f"DraftFailed: {e}"

        # Log each document row for this account (so duplicates are avoided in future)
        for _, r in group.iterrows():
            new_entry = {
                "AccountNumber": r.get('AccountNumber'),
                "ReviewType": r.get('RequestType'),
                "DocumentName": r.get('DocumentName'),
                "Rule": r.get('Rule') if 'Rule' in r.index else None,
                "EmailDate": datetime.now(),
                "To": to_address,
                "CC": ";".join(cc_addresses),
                "Subject": mail.Subject if 'mail' in locals() else None,
                "Status": status
            }
            email_log = pd.concat([email_log, pd.DataFrame([new_entry])], ignore_index=True)

        # persist log after each account to reduce duplication risk
        save_email_log(email_log)

# -------------------------
# MAIN
# -------------------------
def main():
    try:
        logging.info("=== DocDeficiency Automation started ===")

        # 1) Run VBS and get refreshed workbook
        run_vbs_and_rename()

        # 2) Read the refreshed workbook and transform into flat rows
        if not os.path.exists(OUTPUT_FILE):
            logging.error(f"REFRESHED OUTPUT_FILE not found at {OUTPUT_FILE}")
            return

        raw_df = safe_read_excel(OUTPUT_FILE)
        flat_df = transform_doc_deficiency(raw_df)
        flat_df.to_excel(FLAT_FILE, index=False)
        logging.info(f"Flat file saved: {FLAT_FILE}")

        # 3) Read mapping config
        if not os.path.exists(MAPPINGS_FILE):
            logging.error(f"Mapping config not found: {MAPPINGS_FILE}")
            return
        mapping_df = safe_read_excel(MAPPINGS_FILE)

        # 4) Protocol mapping
        protocol_df = protocol_mapping(flat_df, mapping_df)
        logging.info("Protocol mapping complete.")

        # 5) RM enrichment
        enriched = enrich_with_rm(protocol_df)
        enriched.to_excel(PROTOCOL_OUTPUT_FILE, index=False)
        logging.info(f"Protocol + RM output saved: {PROTOCOL_OUTPUT_FILE}")

        # 6) Draft emails (only drafts)
        draft_emails(enriched)

        logging.info("=== DocDeficiency Automation completed successfully ===")
    except Exception as exc:
        logging.exception(f"Unhandled error in automation: {exc}")

if __name__ == "__main__":
    main()