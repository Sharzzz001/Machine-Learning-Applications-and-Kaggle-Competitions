# To (RM)
rm_email = str(group['RM'].iloc[0]).strip() if pd.notnull(group['RM'].iloc[0]) else None

# Build CC list safely
cc_addresses = []
if "YES" in group['Escalation TH'].values and pd.notnull(group['Team Head'].iloc[0]):
    cc_addresses.append(str(group['Team Head'].iloc[0]).strip())
if "YES" in group['Escalation GH'].values and pd.notnull(group['Group Head'].iloc[0]):
    cc_addresses.append(str(group['Group Head'].iloc[0]).strip())

# Deduplicate and remove RM if also in CC
cc_addresses = list(set([a for a in cc_addresses if a]))
if rm_email in cc_addresses:
    cc_addresses.remove(rm_email)

# Assign addresses
if rm_email:
    mail.To = rm_email
if cc_addresses:
    mail.CC = ";".join(cc_addresses)