import pandas as pd
from tqdm import tqdm
from collections import Counter
import logging

# Set up logging
logging.basicConfig(filename="error_sequence_analysis.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

def extract_individual_errors(df):
    """Extract individual errors per region"""
    region_errors = df.groupby('Region')['Error description'].apply(set).to_dict()
    return region_errors

def find_common_and_unique_errors(region_errors):
    """Find common and unique errors across regions"""
    all_errors = set.union(*region_errors.values())
    common_errors = set.intersection(*region_errors.values())
    
    unique_errors = {region: errors - common_errors for region, errors in region_errors.items()}
    
    return common_errors, unique_errors

def save_results(region_patterns, region_errors, common_errors, unique_errors, output_path="error_sequence_analysis.xlsx"):
    """Save the results to an Excel file"""
    with pd.ExcelWriter(output_path) as writer:
        # Save sequence results
        for region, sequences in region_patterns.items():
            sequence_data = []
            
            for (error_seq, nack_seq), count in sequences.items():
                num_errors = len(error_seq.split(' -> '))
                total_errors = num_errors * count
                
                sequence_data.append((error_seq, nack_seq, count, num_errors, total_errors))

            # Create a DataFrame for sequences
            df = pd.DataFrame(sequence_data, 
                              columns=['Full Error Sequence', 'Full Nack Sequence', 'Count', 
                                       'Errors per Sequence', 'Total Errors'])
            df = df.sort_values(by='Total Errors', ascending=False)
            df.to_excel(writer, sheet_name=f"{region}_Full_Sequences", index=False)

        # Save common errors
        common_df = pd.DataFrame({'Common Errors': list(common_errors)})
        common_df.to_excel(writer, sheet_name="Common Errors", index=False)

        # Save unique errors per region
        unique_error_data = [(region, error) for region, errors in unique_errors.items() for error in errors]
        unique_df = pd.DataFrame(unique_error_data, columns=['Region', 'Unique Error'])
        unique_df.to_excel(writer, sheet_name="Unique Errors", index=False)

    logging.info(f"Results saved to {output_path}")

def main(file_path):
    """Main function to orchestrate the analysis"""
    try:
        df = pd.read_excel(file_path)

        # Validate necessary columns
        required_columns = {'Region', 'UTI ref', 'Error description', 'Nack Type'}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"Missing required columns: {required_columns - set(df.columns)}")

        # Extract individual errors per region
        region_errors = extract_individual_errors(df)

        # Find common and unique errors
        common_errors, unique_errors = find_common_and_unique_errors(region_errors)

        # Save results
        output_path = f"error_sequence_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        save_results({}, region_errors, common_errors, unique_errors, output_path)

        print(f"Analysis complete! Results saved to {output_path}")

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    file_path = input("Enter the path to the Excel file: ")
    main(file_path)