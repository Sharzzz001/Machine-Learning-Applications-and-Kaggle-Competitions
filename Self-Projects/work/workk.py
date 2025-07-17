column_mapping = {
    'AccountNumber': 'Account no',
    'RequestType': 'Request type',
    'InitialTargetDate': 'Initial Target Date',

    # Document 1
    'DocName1': 'Document1',
    'DocType1': 'Document Deficiency Type 1',
    'DefiStartDate1': 'Doc defic Start date 1',
    'DocStatus1': 'Document Status 1',
    'ExtendedDeadline1': 'Extended Deadline 1',

    # Document 2
    'DocName2': 'Document2',
    'DocType2': 'Document Deficiency Type 2',
    'DefiStartDate2': 'Doc defic Start date 2',
    'DocStatus2': 'DocumentStatus2',  # Example without space
    'ExtendedDeadline2': 'Extended Deadline 2',

    # Document 3
    'DocName3': 'Document3',
    'DocType3': 'Document Deficiency Type 3',
    'DefiStartDate3': 'Doc defic Start date 3',
    'DocStatus3': 'Document Status 3',
    'ExtendedDeadline3': 'Extended Deadline 3',

    # Document 4
    'DocName4': 'Document4',
    'DocType4': 'Document Deficiency Type 4',
    'DefiStartDate4': 'Doc defic Start date 4',
    'DocStatus4': 'Document Status 4',
    'ExtendedDeadline4': 'Extended Deadline 4',

    # Document 5
    'DocName5': 'Document5',
    'DocType5': 'Document Deficiency Type 5',
    'DefiStartDate5': 'Doc defic Start date 5',
    'DocStatus5': 'Document Status 5',
    'ExtendedDeadline5': 'Extended Deadline 5',
}


import pandas as pd

def transform_doc_deficiency(df, column_mapping):
    transformed_rows = []

    for idx, row in df.iterrows():
        account = row[column_mapping['AccountNumber']]
        request_type = row[column_mapping['RequestType']]
        initial_target = row[column_mapping['InitialTargetDate']]

        # Process each of the 5 documents explicitly
        for doc_slot in range(1, 6):
            doc_name_col = column_mapping.get(f'DocName{doc_slot}')
            if pd.isnull(row[doc_name_col]):
                continue  # Skip empty document slots

            record = {
                'AccountNumber': account,
                'RequestType': request_type,
                'DocumentName': row[doc_name_col],
                'DocDefiType': row[column_mapping[f'DocType{doc_slot}']],
                'DocDefiStartDate': row[column_mapping[f'DefiStartDate{doc_slot}']],
                'DocumentStatus': row[column_mapping[f'DocStatus{doc_slot}']],
                'InitialTargetDate': initial_target,
                'ExtendedDeadline': row[column_mapping[f'ExtendedDeadline{doc_slot}']]
            }
            transformed_rows.append(record)

    return pd.DataFrame(transformed_rows)
    

# Read your SharePoint export
df = pd.read_excel('sharepoint_snapshot.xlsx')

# Apply transformation
flat_df = transform_doc_deficiency(df, column_mapping)

# Output to check
print(flat_df.head())