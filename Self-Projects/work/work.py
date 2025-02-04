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
def merge_training_data(existing_train_path, new_train_path):
    """Merges old training data with new training data."""
    if os.path.exists(existing_train_path):
        existing_train = pd.read_csv(existing_train_path)
    else:
        existing_train = pd.DataFrame()

    new_train = pd.read_csv(new_train_path)

    final_train = pd.concat([existing_train, new_train], ignore_index=True)
    return final_train


@FunctionLogger
def process_target_columns(train_df, data2_path, data3_path, data4_path):
    """Creates two target columns using Data2 & Data3 for Model1 and Data4 for Model2."""
    data2 = pd.read_csv(data2_path)
    data3 = pd.read_csv(data3_path)
    data4 = pd.read_csv(data4_path)

    # Create Target for Model1
    train_df["target_model1"] = data2["col1"] + data3["col2"]  # Modify logic as per requirement

    # Create Target for Model2
    train_df["target_model2"] = data4["col3"]  # Modify logic as per requirement

    return train_df


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
    # Merge old and new training data
    merged_train_data = merge_training_data(args.existing_train, args.new_train1)

    # Add target columns
    final_train_data = process_target_columns(merged_train_data, args.new_train2, args.new_train3, args.new_train4)

    # Save new training data with a timestamp
    new_train_path = save_training_data(final_train_data, args.existing_train)
    print(f"Updated training data saved to {new_train_path}")

    # Train Model 1 and Model 2
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
