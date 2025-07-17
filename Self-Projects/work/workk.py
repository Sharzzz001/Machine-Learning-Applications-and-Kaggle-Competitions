import pandas as pd
import datetime

def calculate_age(start_date, extended_deadline=None):
    today = datetime.date.today()
    if pd.notnull(extended_deadline):
        start = pd.to_datetime(extended_deadline).date()
    else:
        start = pd.to_datetime(start_date).date()
    return (today - start).days

def transform_doc_deficiency_with_flags(df, column_mapping):
    transformed_rows = []
    today = datetime.date.today()

    for idx, row in df.iterrows():
        account = row[column_mapping['AccountNumber']]
        request_type = row[column_mapping['RequestType']]
        initial_target = row[column_mapping['InitialTargetDate']]

        for doc_slot in range(1, 6):
            doc_name_col = column_mapping.get(f'DocName{doc_slot}')
            if pd.isnull(row[doc_name_col]):
                continue

            doc_name = row[doc_name_col]
            doc_type = row[column_mapping[f'DocType{doc_slot}']]
            defi_start = row[column_mapping[f'DefiStartDate{doc_slot}']]
            doc_status = row[column_mapping[f'DocStatus{doc_slot}']]
            ext_deadline = row[column_mapping[f'ExtendedDeadline{doc_slot}']]

            age = calculate_age(defi_start, ext_deadline)

            record = {
                'AccountNumber': account,
                'RequestType': request_type,
                'DocumentName': doc_name,
                'DocDefiType': doc_type,
                'DocDefiStartDate': defi_start,
                'DocumentStatus': doc_status,
                'InitialTargetDate': initial_target,
                'ExtendedDeadline': ext_deadline,
                'Age': age,
                # Escalation flags to be initialized or updated in DB later
                'LastEscalationLevel': 0,  # Assume 0 if first time (update if exists in Access)
                'LastEscalationDate': None,
                'CurrentStatus': 'Open' if doc_status != 'Completed' else 'Closed',
                'PendingForClosure': 'Yes' if age >= 120 and doc_status != 'Completed' else 'No'
            }

            transformed_rows.append(record)

    return pd.DataFrame(transformed_rows)