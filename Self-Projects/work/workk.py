import pandas as pd
import datetime

# === Load Input Files ===
flat_df = pd.read_excel("flat_df.xlsx")
mapping_df = pd.read_excel("mapping_df.xlsx")

# === Helper: Calculate Due Days (Today - Due Date) ===
def calculate_due_days(initial_target, extended_deadline):
    today = datetime.date.today()
    due_date = pd.to_datetime(extended_deadline if pd.notnull(extended_deadline) else initial_target, errors='coerce')
    if pd.isnull(due_date):
        return None
    return (today - due_date.date()).days  # Positive = overdue, Negative = future

# === Apply Derived Fields ===
flat_df['DueDays'] = flat_df.apply(
    lambda row: calculate_due_days(row['InitialTargetDate'], row['ExtendedDeadline']),
    axis=1
)

flat_df['Fcc Extension received'] = flat_df['ExtendedDeadline'].apply(
    lambda x: 'Yes' if pd.notnull(x) else 'No'
)

# === Prepare Output Container ===
output_rows = []

# === Matching Loop ===
for _, flat_row in flat_df.iterrows():
    # Apply all conditions
    matched_rows = mapping_df[
        (mapping_df['Process Type'].str.strip().str.upper() == flat_row['Request Type'].strip().upper()) &
        (mapping_df['Doc Type'].str.strip().str.upper() == flat_row['DocDefiType'].strip().upper()) &
        (
            (mapping_df['Fcc Extension received'].str.upper() == 'ANY') |
            (mapping_df['Fcc Extension received'].str.upper() == flat_row['Fcc Extension received'].upper())
        ) &
        (flat_row['DueDays'] >= mapping_df['DueInMin']) &
        (flat_row['DueDays'] <= mapping_df['DueInMax'])
    ]

    if matched_rows.empty:
        # No match → include input row with 'Matched = No'
        output_row = flat_row.to_dict()
        output_row['Matched'] = 'No'
        output_rows.append(output_row)
    else:
        for _, match in matched_rows.iterrows():
            output_row = flat_row.to_dict()
            output_row['Matched'] = 'Yes'
            # Append escalation flags from mapping
            for col in match.index:
                if col not in ['Process Type', 'Doc Type', 'DueInMin', 'DueInMax', 'Fcc Extension received']:
                    output_row[col] = match[col]
            output_rows.append(output_row)

# === Create Output DataFrame ===
output_df = pd.DataFrame(output_rows)

# === Export to Excel ===
output_df.to_excel("protocol_mapping_output.xlsx", index=False)

print("✅ Mapping complete. Output saved to 'protocol_mapping_output.xlsx'")