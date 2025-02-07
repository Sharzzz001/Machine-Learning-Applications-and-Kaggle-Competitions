import argparse
import os
import time
import psutil
import pandas as pd
import traceback
from datetime import datetime
from autogluon.tabular import TabularPredictor
import logging

# Setup logging
log_filename = f"training_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Performance Logger with Error Handling
class FunctionLogger:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        start_time = time.time()
        process = psutil.Process(os.getpid())

        cpu_before = psutil.cpu_percent(interval=None)
        mem_before = process.memory_info().rss / (1024 * 1024)  # Convert to MB

        try:
            result = self.func(*args, **kwargs)
        except Exception as e:
            error_message = (
                f"Error in function: {self.func.__name__}\n"
                f"Exception: {str(e)}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            logging.error(error_message)
            print(error_message)
            result = None
        finally:
            cpu_after = psutil.cpu_percent(interval=None)
            mem_after = process.memory_info().rss / (1024 * 1024)  # Convert to MB
            execution_time = time.time() - start_time

            log_message = (
                f"Function: {self.func.__name__} | "
                f"Execution Time: {execution_time:.2f}s | "
                f"CPU: {cpu_before:.2f}% → {cpu_after:.2f}% | "
                f"Memory: {mem_before:.2f}MB → {mem_after:.2f}MB"
            )

            logging.info(log_message)
            print(log_message)

        return result


@FunctionLogger
def preprocess_new_data(new_train_path, data2_path, data3_path, data4_path):
    """Processes new training data and creates target columns before merging."""
    new_train = pd.read_csv(new_train_path)
    data2 = pd.read_csv(data2_path)
    data3 = pd.read_csv(data3_path)
    data4 = pd.read_csv(data4_path)

    # Ensure merging on the right keys (modify as needed)
    new_train = new_train.merge(data2, on="BPKey", how="left").merge(data3, on="BPKey", how="left")
    new_train = new_train.merge(data4, on="BPKey", how="left")

    # Create target columns
    new_train["target_model1"] = new_train["col1"] + new_train["col2"]  # Adjust logic as needed
    new_train["target_model2"] = new_train["col3"]  # Adjust logic as needed

    return new_train


@FunctionLogger
def merge_training_data(existing_train_path, preprocessed_new_data):
    """Merges existing training data with preprocessed new data."""
    if os.path.exists(existing_train_path):
        existing_train = pd.read_csv(existing_train_path)
    else:
        existing_train = pd.DataFrame()

    final_train = pd.concat([existing_train, preprocessed_new_data], ignore_index=True)
    return final_train


@FunctionLogger
def save_training_data(final_train_data, existing_train_path):
    """Saves the final training dataset in the same folder as the existing training file."""
    existing_dir = os.path.dirname(existing_train_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_train_filename = f"training_data_{timestamp}.csv"
    new_train_path = os.path.join(existing_dir, new_train_filename)

    final_train_data.to_csv(new_train_path, index=False)
    return new_train_path


@FunctionLogger
def train_autogluon_model1(train_data, model_path):
    """Trains Model 1 using 'target_model1' and saves it in the Model1 folder."""
    model1_path = os.path.join(model_path, "Model1")
    os.makedirs(model1_path, exist_ok=True)

    predictor = TabularPredictor(label="target_model1", path=model1_path).fit(train_data)
    return predictor


@FunctionLogger
def train_autogluon_model2(train_data, model_path):
    """Trains Model 2 using 'target_model2' and saves it in the Model2 folder."""
    model2_path = os.path.join(model_path, "Model2")
    os.makedirs(model2_path, exist_ok=True)

    predictor = TabularPredictor(label="target_model2", path=model2_path).fit(train_data)
    return predictor


@FunctionLogger
def main(args):
    """Main function to execute data processing and model retraining."""
    # Step 1: Preprocess new data to create target columns
    preprocessed_new_data = preprocess_new_data(args.new_train1, args.new_train2, args.new_train3, args.new_train4)

    # Step 2: Merge with existing training data
    final_train_data = merge_training_data(args.existing_train, preprocessed_new_data)

    # Step 3: Save new training data with a timestamp
    new_train_path = save_training_data(final_train_data, args.existing_train)
    print(f"Updated training data saved to {new_train_path}")

    # Step 4: Train Model 1 and Model 2
    train_autogluon_model1(final_train_data, args.model_path)
    train_autogluon_model2(final_train_data, args.model_path)

    print(f"Models saved in {args.model_path}/Model1 and {args.model_path}/Model2")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrain two Autogluon models with new data.")

    parser.add_argument("--model_path", type=str, required=True, help="Path to store the updated models.")
    parser.add_argument("--existing_train", type=str, required=True, help="Path to the existing training data file.")
    parser.add_argument("--new_train1", type=str, required=True, help="Path to new main training data file.")
    parser.add_argument("--new_train2", type=str, required=True, help="Path to Data 2 (used for Model1's target).")
    parser.add_argument("--new_train3", type=str, required=True, help="Path to Data 3 (used for Model1's target).")
    parser.add_argument("--new_train4", type=str, required=True, help="Path to Data 4 (used for Model2's target).")

    args = parser.parse_args()

    main(args)
    
    
@FunctionLogger
def preprocess_new_data(new_train_path, data2_path, data3_path, data4_path):
    """Processes new training data and creates target columns before merging."""
    new_train = pd.read_csv(new_train_path)
    data2 = pd.read_csv(data2_path)
    data3 = pd.read_csv(data3_path)
    data4 = pd.read_csv(data4_path)

    # Extract glossref values from Data 2 and Data 3
    glossref_set = set(pd.concat([data2["glossref"], data3["glossref"]], ignore_index=True).dropna().unique())

    # Create target_model1 based on glossref matching
    new_train["target_model1"] = new_train["glossref"].apply(lambda x: "Failure" if x in glossref_set else "Success")

    # Create target_model2 (logic needs to be defined based on Data 4)
    new_train["target_model2"] = new_train["col3"]  # Adjust logic as needed

    return new_train


import os
from tqdm import tqdm

def get_folder_size(folder):
    """Calculate total size of a folder, including all subfiles and subfolders."""
    total_size = 0
    for dirpath, _, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):  # Avoid broken symlinks
                total_size += os.path.getsize(fp)
    return total_size

def scan_drive_or_folder(path):
    """Scans the given path and lists subfolders with their sizes."""
    if not os.path.exists(path):
        print(f"Path '{path}' does not exist!")
        return

    folder_sizes = []
    subfolders = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

    with tqdm(total=len(subfolders), desc="Scanning folders", unit="folder") as pbar:
        for folder in subfolders:
            size = get_folder_size(folder)
            folder_sizes.append((folder, size))
            pbar.update(1)

    # Sort by size in descending order
    folder_sizes.sort(key=lambda x: x[1], reverse=True)

    print("\nTop folders by size:")
    for folder, size in folder_sizes:
        print(f"{folder} - {size / (1024**3):.2f} GB")

if __name__ == "__main__":
    folder_path = input("Enter the drive or folder path to scan: ")
    scan_drive_or_folder(folder_path)


