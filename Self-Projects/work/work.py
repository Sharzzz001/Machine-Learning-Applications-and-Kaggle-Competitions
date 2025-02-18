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
