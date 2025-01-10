import pandas as pd

# Load the Excel file
file_path = "your_excel_file.xlsx"  # Replace with your actual file path
df = pd.read_excel(file_path)

# Calculate 'Total fees'
df['Total fees'] = df['FEE_BASE_CALC'] * df['TOTAL_AMOUNT_CONT'] / 12

# Calculate 'Hypothetical fees'
df['Hypothetical fees'] = df.apply(
    lambda row: 0.00125 * row['TOTAL_AMOUNT_CONT'] / 12 if row['FEE_BASE_CALC'] == 0
    else 0,
    axis=1
)

# Save the updated DataFrame back to an Excel file
output_file = "updated_excel_file.xlsx"  # Replace with your desired output file name
df.to_excel(output_file, index=False)

print(f"Updated Excel file saved to {output_file}")
