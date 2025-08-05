import pandas as pd
import datetime

# === Load Input Files ===
flat_df = pd.read_excel("flat_df.xlsx")
mapping_df = pd.read_excel("mapping_df.xlsx")

# === Prepare flat_df with derived columns ===
def calculate_age(start_date, extended_deadline):
    today = datetime.date.today()
    if pd.notnull(extended_deadline):
        start = pd.to_datetime(extended_deadline, errors='coerce')
    else:
        start = pd.to_datetime(start_date, errors='coerce')
    if pd.isnull(start):
        return None
    return (today - start.date()).days

flat_df['Age'] = flat_df.apply(
    lambda row: calculate_age(row['DocDefiStartDate'], row['ExtendedDeadline']),
    axis=1
)

flat_df['Fcc Extension received'] = flat_df['ExtendedDeadline'].apply(
    lambda x: 'Yes' if pd.notnull(x) else 'No'
)

# === Prepare output DataFrame ===
output_rows = []

for _, flat_row in flat_df.iterrows():
    matched_rows = mapping_df[
        (mapping_df['Process Type'].str.strip().str.upper() == flat_row['Request Type'].strip().upper()) &
        (mapping_df['Doc Type'].str.strip().str.upper() == flat_row['DocDefiType'].strip().upper()) &
        (
            (mapping_df['Fcc Extension received'].str.upper() == flat_row['Fcc Extension received'].upper()) |
            (mapping_df['Fcc Extension received'].str.upper() == 'ANY')
        ) &
        (flat_row['Age'] >= mapping_df['DueInMin']) &
        (flat_row['Age'] <= mapping_df['DueInMax'])
    ]

    if matched_rows.empty:
        # No match → add row with escalation columns as NaN
        output_row = flat_row.to_dict()
        output_row['Matched'] = 'No'
        output_rows.append(output_row)
    else:
        # For each match, append result
        for _, match in matched_rows.iterrows():
            output_row = flat_row.to_dict()
            output_row['Matched'] = 'Yes'
            for col in match.index:
                if col not in ['Process Type', 'Doc Type', 'DueInMin', 'DueInMax', 'Fcc Extension received']:
                    output_row[col] = match[col]
            output_rows.append(output_row)

# === Save final output ===
output_df = pd.DataFrame(output_rows)
output_df.to_excel("protocol_mapping_output.xlsx", index=False)

print("✅ Mapping complete. Output saved to 'protocol_mapping_output.xlsx'")