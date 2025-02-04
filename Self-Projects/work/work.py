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

# Performance Logger Wrapper Class with Error Handling
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
            result = None  # Return None if the function fails
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
def merge_training_data(existing_train_path, new_train_path, data2_path, data3_path, data4_path):
    """Merges old training data with new training data and processes Data2-4 to create the target column."""
    if os.path.exists(existing_train_path):
        existing_train = pd.read_csv(existing_train_path)
    else:
        existing_train = pd.DataFrame()

    new_train = pd.read_csv(new_train_path)
    data2 = pd.read_csv(data2_path)
    data3 = pd.read_csv(data3_path)
    data4 = pd.read_csv(data4_path)

    new_train["target"] = process_target_column(new_train, data2, data3, data4)
    final_train = pd.concat([existing_train, new_train], ignore_index=True)

    return final_train

@FunctionLogger
def process_target_column(train_df, data2, data3, data4):
    """Process Data2, Data3, and Data4 to generate the target column."""
    target = data2['col1'] + data3['col2'] - data4['col3']  # Modify logic as per requirement
    return target

@FunctionLogger
def train_autogluon_model(train_data, save_path):
    """Trains an Autogluon model on the provided dataset and saves it."""
    os.makedirs(save_path, exist_ok=True)
    target_col = "target"

    predictor = TabularPredictor(label=target_col, path=save_path).fit(train_data)
    return predictor

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
def main(args):
    """Main function to execute data processing and model retraining."""
    final_train_data = merge_training_data(
        args.existing_train, args.new_train1, args.new_train2, args.new_train3, args.new_train4
    )

    if final_train_data is not None:
        new_train_path = save_training_data(final_train_data, args.existing_train)
        print(f"Updated training data saved to {new_train_path}")

        predictor = train_autogluon_model(final_train_data, args.model_path)
        print(f"Updated Autogluon model saved at {args.model_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrain an Autogluon model with new data.")

    parser.add_argument("--model_path", type=str, required=True, help="Path to store the updated Autogluon model.")
    parser.add_argument("--existing_train", type=str, required=True, help="Path to the existing training data file.")
    parser.add_argument("--new_train1", type=str, required=True, help="Path to new main training data file.")
    parser.add_argument("--new_train2", type=str, required=True, help="Path to Data 2 (used for target column).")
    parser.add_argument("--new_train3", type=str, required=True, help="Path to Data 3 (used for target column).")
    parser.add_argument("--new_train4", type=str, required=True, help="Path to Data 4 (used for target column).")

    args = parser.parse_args()

    main(args)
