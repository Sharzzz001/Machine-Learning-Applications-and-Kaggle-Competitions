import pandas as pd
from tqdm import tqdm
from collections import Counter
import logging

# Set up logging
logging.basicConfig(filename="error_sequence_analysis.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

def clean_sequence(sequence):
    """Clean and normalize the sequence"""
    return ' -> '.join(item.strip() for item in sequence if pd.notnull(item))

def extract_full_sequences(df, region):
    """Extract full error and nack sequences for a given region"""
    region_df = df[df['Region'] == region].sort_values(by='UTI ref')
    sequences = []

    grouped = region_df.groupby('UTI ref').agg({
        'Error description': list,
        'Nack Type': list
    }).reset_index()

    for _, row in grouped.iterrows():
        error_descriptions = row['Error description']
        nack_types = row['Nack Type']

        # Capture full sequences
        if len(error_descriptions) > 0:
            error_seq = clean_sequence(error_descriptions)
            nack_seq = clean_sequence(nack_types)
            sequences.append((error_seq, nack_seq))
    
    return sequences

def analyze_full_sequences(df):
    """Analyze full error and nack sequences for all regions"""
    regions = df['Region'].unique()
    region_patterns = {}

    pbar = tqdm(regions, desc="Analyzing regions")

    for region in pbar:
        try:
            sequences = extract_full_sequences(df, region)
            sequence_counts = Counter(sequences)
            region_patterns[region] = sequence_counts

            # Debugging: Log top sequences
            top_sequences = sequence_counts.most_common(5)
            logging.info(f"Top sequences in {region}: {top_sequences}")

            pbar.set_postfix({"Region": region, "Full Sequences": len(sequence_counts)})
            logging.info(f"Analyzed {region}: {len(sequence_counts)} full sequences")
        
        except Exception as e:
            logging.error(f"Error analyzing region {region}: {e}")

    return region_patterns

def save_results(region_patterns, output_path="error_sequence_analysis.xlsx"):
    """Save the results to an Excel file"""
    with pd.ExcelWriter(output_path) as writer:
        for region, sequences in region_patterns.items():
            sequence_data = []
            
            for (error_seq, nack_seq), count in sequences.items():
                num_errors = len(error_seq.split(' -> '))
                total_errors = num_errors * count
                
                sequence_data.append((error_seq, nack_seq, count, num_errors, total_errors))

            # Create a DataFrame
            df = pd.DataFrame(sequence_data, 
                              columns=['Full Error Sequence', 'Full Nack Sequence', 'Count', 
                                       'Errors per Sequence', 'Total Errors'])
            df = df.sort_values(by='Total Errors', ascending=False)
            df.to_excel(writer, sheet_name=f"{region}_Full_Sequences", index=False)

    logging.info(f"Results saved to {output_path}")

def main(file_path):
    """Main function to orchestrate the analysis"""
    try:
        df = pd.read_excel(file_path)

        # Validate necessary columns
        required_columns = {'Region', 'UTI ref', 'Error description', 'Nack Type'}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"Missing required columns: {required_columns - set(df.columns)}")

        # Run full sequence analysis
        region_patterns = analyze_full_sequences(df)

        # Save results
        output_path = f"error_sequence_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        save_results(region_patterns, output_path)

        print(f"Analysis complete! Results saved to {output_path}")

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    file_path = input("Enter the path to the Excel file: ")
    main(file_path)