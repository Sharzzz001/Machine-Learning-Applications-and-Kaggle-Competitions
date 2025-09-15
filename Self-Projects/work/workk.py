# To (RM)
rm_email = group['RM'].iloc[0]
to_address = rm_email if pd.notnull(rm_email) and str(rm_email).strip() != "" else None

# Build CC list safely
cc_addresses = []
if "YES" in group['Escalation TH'].values and pd.notnull(group['Team Head'].iloc[0]):
    cc_addresses.append(str(group['Team Head'].iloc[0]).strip())
if "YES" in group['Escalation GH'].values and pd.notnull(group['Group Head'].iloc[0]):
    cc_addresses.append(str(group['Group Head'].iloc[0]).strip())

cc_addresses = [a for a in cc_addresses if a]  # filter empties

# Assign
if to_address:
    mail.To = to_address
if cc_addresses:
    mail.CC = ";".join(cc_addresses)