import pandas as pd
from collections import Counter

# Load Excel file
df = pd.read_excel("trade_errors.xlsx")

# Ensure correct column names
df = df[['UTI Ref', 'Action Type', 'Error Description']]  # Adjust column names if needed

# Group by UTI Ref and get ordered sequences of error descriptions
error_sequences = df.groupby('UTI Ref')['Error Description'].apply(list)

# Count frequency of each error sequence
sequence_counts = Counter(tuple(seq) for seq in error_sequences)

# Sort sequences by frequency
sorted_sequences = sorted(sequence_counts.items(), key=lambda x: x[1], reverse=True)

# Convert results into a DataFrame for better visualization
result_df = pd.DataFrame(sorted_sequences, columns=['Error Sequence', 'Count'])

# Save results to Excel
result_df.to_excel("error_sequence_analysis.xlsx", index=False)

# Display top 10 sequences
print(result_df.head(10))



newt_errors = df[df['Action Type'] == 'NEWT']
field_type_counts = newt_errors['Error Description'].value_counts()
print(field_type_counts.head(10))  # Top 10 missing fields



from itertools import combinations
from collections import Counter

# Get all UTI refs that failed multiple times
multi_nack_trades = df[df.duplicated(subset=['UTI Ref'], keep=False)]

# Get error description sequences for each UTI
error_sequences = multi_nack_trades.groupby('UTI Ref')['Error Description'].apply(list)

# Find pairs of errors occurring together
error_pairs = [pair for seq in error_sequences for pair in combinations(seq, 2)]
pair_counts = Counter(error_pairs)

print(pair_counts.most_common(10))  # Top 10 cascading error pairs



failure_counts = df['UTI Ref'].value_counts()
repeat_failures = (failure_counts > 1).sum()
total_trades = len(failure_counts)

print(f"Trades failing multiple times: {repeat_failures}/{total_trades} ({(repeat_failures/total_trades)*100:.2f}%)")



failed_newt = df[df['Action Type'] == 'NEWT']['UTI Ref']
modt_after_newt = df[(df['UTI Ref'].isin(failed_newt)) & (df['Action Type'] == 'MODT')]

print(f"Trades modified after failure: {modt_after_newt['UTI Ref'].nunique()}")




