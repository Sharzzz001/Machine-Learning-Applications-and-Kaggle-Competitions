import pandas as pd
from tqdm import tqdm
from collections import Counter
from itertools import tee, islice
import logging
import os

# Set up logging
logging.basicConfig(filename="error_sequence_analysis.log", level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

def sliding_window(iterable, n):
    """Generate n-length sliding window from iterable"""
    iterables = tee(iterable, n)
    for i, it in enumerate(iterables):
        next(islice(it, i, i), None)
    return zip(*iterables)

def extract_sequences(df, region, sequence_length=3):
    """Extract error sequences for a given region"""
    region_df = df[df['Region'] == region].sort_values(by='UTI ref')
    sequences = []

    grouped = region_df.groupby('UTI ref')['Error description'].apply(list).reset_index()

    for _, row in grouped.iterrows():
        error_descriptions = row['Error description']
        if len(error_descriptions) >= sequence_length:
            sequences.extend([' -> '.join(seq) for seq in sliding_window(error_descriptions, sequence_length)])
    
    return sequences

def analyze_error_sequences(df, sequence_length=3):
    """Analyze error sequences for all regions"""
    regions = df['Region'].unique()
    region_patterns = {}

    pbar = tqdm(regions, desc="Analyzing regions")

    for region in pbar:
        try:
            sequences = extract_sequences(df, region, sequence_length)
            sequence_counts = Counter(sequences)
            region_patterns[region] = sequence_counts

            pbar.set_postfix({"Region": region, "Unique Sequences": len(sequence_counts)})
            logging.info(f"Analyzed {region}: {len(sequence_counts)} unique sequences")
        
        except Exception as e:
            logging.error(f"Error analyzing region {region}: {e}")

    return region_patterns

def compare_regions(region_patterns):
    """Compare sequences across regions"""
    region_sequences = {}

    for region, sequences in region_patterns.items():
        region_sequences[region] = set(sequences.keys())

    common_sequences = set.intersection(*region_sequences.values())
    unique_sequences = {region: seqs - common_sequences for region, seqs in region_sequences.items()}

    return common_sequences, unique_sequences

def save_results(region_patterns, common_sequences, unique_sequences, output_path="error_sequence_analysis.xlsx"):
    """Save the results to an Excel file"""
    with pd.ExcelWriter(output_path) as writer:
        for region, sequences in region_patterns.items():
            df = pd.DataFrame(sequences.items(), columns=['Error Sequence', 'Count'])
            df = df.sort_values(by='Count', ascending=False)
            df.to_excel(writer, sheet_name=f"{region}_Sequences", index=False)

        # Save common sequences
        common_df = pd.DataFrame({'Common Sequences': list(common_sequences)})
        common_df.to_excel(writer, sheet_name="Common Sequences", index=False)

        # Save unique sequences per region
        unique_df = pd.DataFrame([(region, seq) for region, seqs in unique_sequences.items() for seq in seqs], 
                                 columns=['Region', 'Unique Sequence'])
        unique_df.to_excel(writer, sheet_name="Unique Sequences", index=False)

    logging.info(f"Results saved to {output_path}")

def main(file_path, sequence_length=3):
    """Main function to orchestrate the analysis"""
    try:
        df = pd.read_excel(file_path)

        # Validate necessary columns
        required_columns = {'Region', 'UTI ref', 'Error description'}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"Missing required columns: {required_columns - set(df.columns)}")

        # Run analysis
        region_patterns = analyze_error_sequences(df, sequence_length)
        common_sequences, unique_sequences = compare_regions(region_patterns)

        # Save results
        output_path = f"error_sequence_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        save_results(region_patterns, common_sequences, unique_sequences, output_path)

        print(f"Analysis complete! Results saved to {output_path}")

    except Exception as e:
        logging.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    file_path = input("Enter the path to the Excel file: ")
    sequence_length = int(input("Enter the sequence length (default is 3): ") or 3)
    main(file_path, sequence_length)