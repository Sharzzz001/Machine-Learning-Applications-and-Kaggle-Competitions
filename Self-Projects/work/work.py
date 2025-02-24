import pandas as pd
from tqdm import tqdm
from collections import Counter
import logging

# Set up logging
logging.basicConfig(filename="error_description_analysis.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

def count_errors_by_region(df):
    """Count individual errors per region"""
    region_error_counts = df.groupby(['Region', 'Error description']).size().reset_index(name='Count')
    return region_error_counts

def compare_errors_between_regions(region_error_counts):
    """Compare errors across regions to find common and unique errors"""
    region_errors = region_error_counts.groupby('Region')['Error description'].apply(set).to_dict()
    
    # Find common and unique errors
    all_errors = set.union(*region_errors.values())
    common_errors = set.intersection(*region_errors.values())
    unique_errors = {region: errors - common_errors for region, errors in region_errors.items()}
    
    return common_errors, unique_errors

def save_results(region_error_counts, common_errors, unique_errors, output_path="error_description_analysis.xlsx"):
    """Save the results to an Excel file"""
    with pd.ExcelWriter(output_path) as writer:
        # Save error counts per region
        for region, region_df in region_error_counts.groupby('Region'):
            region_df = region_df.sort_values(by='Count', ascending=False)
            region_df.to_excel(writer, sheet_name=f"{region}_Error_Counts", index=False)

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
        required_columns = {'Region', 'Error description'}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"Missing required columns: {required_columns - set(df.columns)}")

        # Count individual errors within each region
        region_error_counts = count_errors_by_region(df)

        # Find common and unique errors across regions
        common_errors, unique_errors = compare_errors_between_regions(region_error_counts)

        # Save results
        output_path = f"error_description_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        save_results(region_error_counts, common_errors, unique_errors, output_path)

        print(f"Analysis complete! Results saved to {output_path}")

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    file_path = input("Enter the path to the Excel file: ")
    main(file_path)