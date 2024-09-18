import pandas as pd
import pdfplumber

# Step 1: Group and sum the Excel data by ISIN and account type
excel_data = pd.read_excel('your_excel_file.xlsx')
grouped_data = excel_data.groupby(['ISIN', 'Account Type'])['Amount'].sum().reset_index()

# Step 2: Function to extract data from PDF
def extract_isin_data_from_pdf(pdf_path, isin):
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if isin in text:
                # Check if 'cash' appears twice
                cash_count = text.lower().count('cash')
                account_type = 'cash' if cash_count >= 2 else 'share'
                
                # Extract table below ISIN
                table = page.extract_table()  # Extract the table as a list of lists
                if table:
                    for row in table:
                        # Assuming amount is in a specific column, e.g., the last column
                        amount = row[-1]  # Adjust index based on the table structure
                        return account_type, float(amount)
    return None, None  # Return None if ISIN is not found

# Step 3: Reconcile the data
reconciliation_results = []

for index, row in grouped_data.iterrows():
    isin = row['ISIN']
    excel_amount = row['Amount']
    account_type_excel = row['Account Type']
    
    account_type_pdf, pdf_amount = extract_isin_data_from_pdf('your_pdf_file.pdf', isin)
    
    if account_type_pdf:
        # Check if account types match
        if account_type_pdf == account_type_excel:
            difference = excel_amount - pdf_amount
            percentage_diff = (difference / pdf_amount) * 100 if pdf_amount else None
            reconciliation_results.append({
                'ISIN': isin,
                'Account Type': account_type_excel,
                'Summed Excel Amount': excel_amount,
                'Extracted PDF Amount': pdf_amount,
                'Difference': difference,
                'Percentage Difference': percentage_diff
            })

# Step 4: Create a DataFrame with the results
reconciliation_df = pd.DataFrame(reconciliation_results)

# Save the reconciliation to Excel
reconciliation_df.to_excel('reconciliation_results.xlsx', index=False)