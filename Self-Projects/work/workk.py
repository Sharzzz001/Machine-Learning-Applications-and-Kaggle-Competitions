import re

# Clean up Remark column
def clean_remark(text):
    if pd.isna(text):
        return text
    text = str(text).strip().lower()

    # standardize dormant remarks
    if text.startswith("dormant since"):
        return "Dormant"

    # standardize total blocking
    if "total blocking" in text:
        return "Total Blocking"

    # standardize transfer blocking
    if "blocked for transfer transactions" in text:
        return "Blocked for Transfer Transactions"

    return text.title()   # keep other remarks nicely formatted