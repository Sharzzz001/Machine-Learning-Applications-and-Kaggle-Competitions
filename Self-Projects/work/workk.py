import win32com.client as win32
import pandas as pd

def build_html_table(df: pd.DataFrame, columns):
    """Builds a simple HTML table from df[columns]."""
    if df.empty:
        return "<p>Nothing to report.</p>"

    # Start table
    html = [
        '<table border="1" cellspacing="0" cellpadding="3">',
        "<tr>" + "".join(f"<th>{col}</th>" for col in columns) + "</tr>"
    ]

    # Rows
    for _, row in df.iterrows():
        html.append(
            "<tr>" +
            "".join(f"<td>{row.get(col, '')}</td>" for col in columns) +
            "</tr>"
        )

    html.append("</table>")
    return "\n".join(html)


def draft_email_for_group(group: pd.DataFrame,
                          account_number: str,
                          request_type: str,
                          to_address: str = "",
                          cc_addresses=None):
    """
    group: dataframe for a single (AccountNumber, RequestType) combo.
    Assumes group has at least 'DocumentName' and whatever columns
    you want to show in the tables.
    """
    if cc_addresses is None:
        cc_addresses = []

    # --- 1) Split into two sets based on DocumentName blank / not blank ---

    # Treat NaN and "" and "   " as blank
    docname_series = group["DocumentName"].astype(str)
    mask_nonblank = docname_series.str.strip() != ""
    mask_blank = ~mask_nonblank

    df_defi = group[mask_nonblank].copy()   # Table 1: normal deficiencies
    df_phys = group[mask_blank].copy()      # Table 2: AO Physical docs (DocumentName blank)

    # --- 2) Build HTML for both tables ---

    # Decide which columns to show in each table (adjust to your real columns)
    cols_table1 = ["AccountNumber", "RequestType", "DocumentName", "DocDefiType", "DocDesc", "DueDays"]
    cols_table2 = ["AccountNumber", "RequestType", "DocDefiType", "DocDesc", "DueDays"]

    # Filter columns that actually exist to avoid KeyErrors
    cols_table1 = [c for c in cols_table1 if c in group.columns]
    cols_table2 = [c for c in cols_table2 if c in group.columns]

    table1_html = build_html_table(df_defi, cols_table1)
    table2_html = build_html_table(df_phys, cols_table2)

    # --- 3) Build full email body ---

    body_parts = []

    # Section 1: normal deficiencies
    body_parts.append("<p>The following account has pending document deficiencies:</p>")
    body_parts.append(table1_html)

    # Section 2: AO Physical documents
    body_parts.append("<br><p>The following account has pending AO Physical Documents:</p>")
    body_parts.append(table2_html)

    body_html = "\n".join(body_parts)

    # --- 4) Draft Outlook email (no timestamp handling, just Save) ---

    outlook = win32.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)  # 0 = Mail item

    mail.Subject = f"Document Deficiency (For Your Attention) - Account {account_number} ({request_type})"
    if to_address:
        mail.To = to_address
    if cc_addresses:
        mail.CC = ";".join(cc_addresses)

    mail.HTMLBody = body_html
    # Optional: sent on behalf, if you use a shared mailbox
    # mail.SentOnBehalfOfName = "iwmkycops@nomura.com"

    mail.Save()  # draft only, no send

    # You can return something if you want to log outside
    return mail