if matched_rows.empty:
    # No match → include input row with 'Matched = No'
    output_row = flat_row.to_dict()
    output_row['Matched'] = 'No'
    output_rows.append(output_row)
elif len(matched_rows) > 1:
    # Multiple matches → print warning
    print(f"⚠️  Account {flat_row['Account Number']} / DocType {flat_row['DocDefiType']} / DueDays {flat_row['DueDays']} matched multiple protocols!")
    for _, match in matched_rows.iterrows():
        output_row = flat_row.to_dict()
        output_row['Matched'] = 'Yes (Multiple)'
        for col in match.index:
            if col not in ['Process Type', 'Doc Type', 'DueInMin', 'DueInMax', 'Fcc Extension received']:
                output_row[col] = match[col]
        output_rows.append(output_row)
else:
    # Exactly one match
    match = matched_rows.iloc[0]
    output_row = flat_row.to_dict()
    output_row['Matched'] = 'Yes'
    for col in match.index:
        if col not in ['Process Type', 'Doc Type', 'DueInMin', 'DueInMax', 'Fcc Extension received']:
            output_row[col] = match[col]
    output_rows.append(output_row)