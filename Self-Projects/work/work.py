import pandas as pd
from collections import defaultdict
from tqdm import tqdm

def get_error_sequences(df):
    """ Group NACK data by UTI ID and return error sequences """
    sequences = defaultdict(list)
    grouped = df.sort_values(by='Date').groupby('UTI ID')

    for uti, group in grouped:
        sequences[uti] = list(group['Error description'])
        
    return sequences

def analyze_jira_impact(df1, df2):
    """ Analyze sequences to check if JIRA release fixed the errors """
    results = []

    # Parse dates
    df1['Release date'] = pd.to_datetime(df1['Release date'])
    df2['Date'] = pd.to_datetime(df2['Date'])

    # Get sequences
    error_sequences = get_error_sequences(df2)

    for _, jira_row in tqdm(df1.iterrows(), total=len(df1)):
        jira_error = jira_row['Error description']
        release_date = jira_row['Release date']
        
        for uti, sequence in error_sequences.items():
            try:
                # Split sequence into before/after release date
                before_release = df2[(df2['UTI ID'] == uti) & (df2['Date'] < release_date)]
                after_release = df2[(df2['UTI ID'] == uti) & (df2['Date'] >= release_date)]

                before_sequence = list(before_release['Error description'])
                after_sequence = list(after_release['Error description'])

                # Check if the JIRA error is the **first error** in the sequence
                if before_sequence and before_sequence[0] == jira_error:
                    # If the error disappears **after release**, tag it as fixed
                    fixed = jira_error not in after_sequence

                    results.append({
                        'UTI ID': uti,
                        'JIRA Error': jira_error,
                        'Release Date': release_date,
                        'Before Sequence': " -> ".join(before_sequence),
                        'After Sequence': " -> ".join(after_sequence) if after_sequence else "None",
                        'Fixed After Release': 'Yes' if fixed else 'No'
                    })
            except Exception as e:
                print(f"Error processing UTI {uti}: {e}")

    return pd.DataFrame(results)

# Load your data
jira_df = pd.read_excel("jira_data.xlsx")
nack_df = pd.read_excel("nack_data.xlsx")

# Run the analysis
result_df = analyze_jira_impact(jira_df, nack_df)

# Save results
result_df.to_excel("jira_error_fix_analysis.xlsx", index=False)
print("Analysis complete! Results saved to 'jira_error_fix_analysis.xlsx'")